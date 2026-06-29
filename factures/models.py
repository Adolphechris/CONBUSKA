import decimal
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.db.models import Max, Count, Sum, F, DecimalField
from django.db.models.functions import TruncDate
from django.utils import timezone
import datetime


class Livreur(models.Model):
    nom = models.CharField(max_length=30)
    livraison = models.IntegerField(default=0)
    def __str__(self):
        return self.nom


class FactureManager(models.Manager):
    def ventes_journalieres(self, date_debut=None, date_fin=None):
        today = timezone.now().date()
        if date_debut is None:
            date_debut = today
        if date_fin is None:
            date_fin = today
        return (self.get_queryset()
                .filter(date_facture__range=(date_debut, date_fin))
                .annotate(date=TruncDate('date_facture'))
                .values('date')
                .annotate(
                    nb_factures=Count('id', distinct=True),
                    total_vendu=Sum(
                        F('facture_details__qte') * F('facture_details__prix'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ) - Sum('remise', distinct=True)
                )
                .order_by('date'))


class Facture(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    numero = models.IntegerField(unique=True, blank=False)
    date_facture = models.DateField(default=datetime.date.today)
    devise = models.CharField(max_length=2, choices=DEVISES)
    taux = models.DecimalField(default=0.0, max_digits=6, decimal_places=2)
    remise = models.DecimalField(default=0, max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    client_comptoir = models.CharField(max_length=30, null=True, blank=True)
    livreur = models.ForeignKey(Livreur, on_delete=models.PROTECT, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey('users.CustomUser',
                                 related_name='facturecreepar',
                                 on_delete=models.PROTECT)
    modifie_par = models.ForeignKey('users.CustomUser',
                                    blank=True, null=True,
                                    related_name='facturemodpar',
                                    on_delete=models.PROTECT)
    actif = models.BooleanField(default=True)
    valide = models.BooleanField(default=False)
    valeur_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    objects = FactureManager()

    def __str__(self):
        return str(self.numero)

    @property
    def sous_total(self):
        # Si la facture n'est pas encore sauvegardée (pas de PK), pas de détails en DB
        if not self.pk:
            return decimal.Decimal(0)
        
        result = DetailsFacture.objects.filter(facture=self) \
            .annotate(sub=F("qte") * F("prix")) \
            .aggregate(total=Sum("sub"))["total"]

        return result or decimal.Decimal(0)

    @property
    def total(self):
        return self.sous_total - self.remise

    @property
    def total_devise(self):
        return self.total / self.taux

    @property
    def total_articles(self):
        # Si la facture n'est pas encore sauvegardée (pas de PK), pas de détails en DB
        if not self.pk:
            return 0
        return DetailsFacture.objects.filter(facture=self.pk).count()

    @classmethod
    def get_next_num(cls):
        with transaction.atomic():
            last_num = cls.objects.select_for_update().aggregate(Max("numero"))["numero__max"]
        if last_num:
            return last_num + 1
        return int(timezone.now().strftime("%y") + "0000")

    def clean(self):
        """Verrouille le taux et la valeur USD une fois la facture validée."""
        if self.valide:
            if self.taux is None or self.taux == Decimal('0'):
                raise ValidationError("Le taux doit être défini pour toute facture validée.")

            if self.devise not in dict(self.DEVISES):
                raise ValidationError("La devise de la facture doit être USD ou FC.")

            if self.pk:
                original = Facture.objects.filter(pk=self.pk).first()
                if original and original.valide:
                    if self.devise != original.devise:
                        raise ValidationError("La devise d'une facture validée ne peut pas être modifiée.")
                    if self.taux != original.taux:
                        raise ValidationError("Le taux d'une facture validée ne peut pas être modifié.")

            # Validation du stock par lots
            self._valider_stock_lots()

            if self.devise == '$':
                if self.valeur_usd not in (None, self.total):
                    raise ValidationError("La valeur USD d'une facture en USD doit correspondre au total.")
            else:
                expected_usd = self.total / self.taux if self.taux else Decimal('0')
                if self.valeur_usd is not None and self.valeur_usd != expected_usd:
                    raise ValidationError(
                        "La valeur USD enregistrée doit être cohérente avec le total FC et le taux historique."
                    )

        return super().clean()

    def _valider_stock_lots(self):
        """
        Valide et consomme le stock par lots lors de la validation de facture.
        
        RÈGLES:
        - Si lot est renseigné → vérifier stock suffisant sur CE lot
        - Si lot est NULL → FIFO automatique sur date_peremption
        - 1 ligne = N MouvementStock (traçabilité complète)
        """
        from produits.services.stock_service import StockService
        
        for ligne in self.facture_details.all():
            article = ligne.article
            qte = ligne.qte
            
            if ligne.lot:
                # Cas 1: Lot explicite → vérifier CE lot uniquement
                from produits.models import Stock
                try:
                    stock_lot = Stock.objects.get(
                        magasin__is_principal=True,
                        article=article,
                        date_peremption=ligne.lot.date_peremption
                    )
                except Stock.DoesNotExist:
                    raise ValidationError(
                        f"Lot introuvable pour '{article}' (péremption {ligne.lot.date_peremption})."
                    )
                
                if stock_lot.qte < qte:
                    raise ValidationError(
                        f"Stock insuffisant pour '{article}' (lot {ligne.lot.date_peremption}) : "
                        f"disponible {stock_lot.qte}, demandé {qte}."
                    )
                
                # Débiter le lot
                StockService.sortir_stock_lot(
                    magasin=stock_lot.magasin,
                    article=article,
                    date_peremption=ligne.lot.date_peremption,
                    qte=qte,
                    source=self
                )
            else:
                # Cas 2: Pas de lot → FIFO automatique
                from parametres.models import Magasin
                magasin_principal = Magasin.objects.filter(is_principal=True).first()
                if not magasin_principal:
                    raise ValidationError("Aucun magasin principal configuré.")
                
                mouvements = StockService.sortir_stock_fifo(
                    magasin=magasin_principal,
                    article=article,
                    qte=qte,
                    source=self
                )
                
                # Lier le premier mouvement à la ligne (pour traçabilité)
                if mouvements:
                    from produits.models import Stock
                    try:
                        lot_stock = Stock.objects.get(
                            magasin=magasin_principal,
                            article=article,
                            date_peremption=mouvements[0].date_peremption
                        )
                        ligne.lot = lot_stock
                        ligne.save(update_fields=['lot'])
                    except Stock.DoesNotExist:
                        pass

    def save(self, *args, **kwargs):
        if self.numero is None:
            self.numero = self.get_next_num()

        if self.valide:
            self.full_clean()
            tot = self.total
            if self.devise == '$':
                valeur = tot
            else:
                valeur = tot / self.taux if self.taux else Decimal('0')

            self.valeur_usd = valeur

        super(Facture, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('facture_details', args=[self.pk])


class DetailsFacture(models.Model):
    facture = models.ForeignKey(Facture, related_name='facture_details', on_delete=models.PROTECT, null=True)
    article = models.ForeignKey('produits.Article', on_delete=models.PROTECT, null=True)
    lot = models.ForeignKey('produits.Stock', on_delete=models.PROTECT, null=True, blank=True,
                            help_text="Lot spécifique vendu (pour gestion des péremptions)")
    qte = models.IntegerField()
    prix = models.DecimalField(max_digits=12, decimal_places=2)
    valeur_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True,
                                     help_text="Valeur USD historique de cette ligne de facture")
    taux_creation = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True,
                                        help_text="Taux de change historique au moment de la facture")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    @property
    def total(self):
        return self.qte * self.prix

    def save(self, *args, **kwargs):
        from decimal import Decimal
        from parametres.models import get_taux_usd_cdf

        creating = self.pk is None
        if creating and self.valeur_usd is None:
            if self.facture and self.facture.devise:
                montant_ligne = Decimal(str(self.qte)) * Decimal(str(self.prix))
                if self.facture.devise == '$':
                    self.valeur_usd = montant_ligne
                    self.taux_creation = self.facture.taux or get_taux_usd_cdf(self.facture.date_facture)
                else:
                    taux = self.facture.taux or get_taux_usd_cdf(self.facture.date_facture)
                    self.taux_creation = taux
                    self.valeur_usd = montant_ligne / taux if taux else Decimal('0')
        else:
            original = DetailsFacture.objects.filter(pk=self.pk).first()
            if original:
                self.valeur_usd = original.valeur_usd
                self.taux_creation = original.taux_creation
        super().save(*args, **kwargs)


class FactureClient(models.Model):
    facture = models.OneToOneField(Facture, related_name='facture_client', on_delete=models.PROTECT)
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT)
