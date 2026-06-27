from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.db import transaction
from django.db.models import Max, Sum
import datetime


class TypeFrais(models.Model):
    nom = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="fa-money")
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.nom


class Approvisionnement(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    numero = models.IntegerField(unique=True, blank=False)
    magasin = models.ForeignKey('parametres.Magasin', on_delete=models.PROTECT, null=False)
    devise = models.CharField(max_length=2, choices=DEVISES)
    taux = models.DecimalField(default=0.0, max_digits=6, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey('users.CustomUser',
                                 related_name='approvisionnementcreepar',
                                 on_delete=models.PROTECT)
    modifie_par = models.ForeignKey('users.CustomUser',
                                    blank=True, null=True,
                                    related_name='approvisionnementmodpar',
                                    on_delete=models.PROTECT)
    actif = models.BooleanField(default=True)
    valide = models.BooleanField(default=False)
    objects = models.Manager()

    def __str__(self):
        return str(self.numero)

    @property
    def total_approvisionnement(self):
        return sum(i.prix_total for i in self.detailsapprovisionnement_set.all())

    @property
    def frais_achat_total(self):
        return sum(i.frais_achat * i.qte for i in self.detailsapprovisionnement_set.all())

    @property
    def cout_achat(self):
        return sum(i.cout_achat * i.qte for i in self.detailsapprovisionnement_set.all())

    @property
    def resultat_total(self):
        return sum(i.resultat for i in self.detailsapprovisionnement_set.all())

    @property
    def chiffre_affaires(self):
        return sum(i.prix_vente * i.qte for i in self.detailsapprovisionnement_set.all())

    @classmethod
    def get_next_num(cls):
        with transaction.atomic():
            last = cls.objects.select_for_update().aggregate(Max("numero"))["numero__max"]
            return (last + 1) if last else int(datetime.datetime.now().strftime('%y') + '0000')

    def clean(self):
        if self.valide:
            if self.taux is None or self.taux == Decimal('0'):
                raise ValidationError("Le taux doit être défini pour tout approvisionnement validé.")
            if self.devise not in dict(self.DEVISES):
                raise ValidationError("La devise de l'approvisionnement doit être USD ou FC.")

            if self.pk:
                original = Approvisionnement.objects.filter(pk=self.pk).first()
                if original and original.valide:
                    if self.devise != original.devise:
                        raise ValidationError("La devise d'un approvisionnement validé ne peut pas être modifiée.")
                    if self.taux != original.taux:
                        raise ValidationError("Le taux d'un approvisionnement validé ne peut pas être modifié.")

        return super().clean()

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero:
            self.numero = self.get_next_num()

        if self.valide:
            self.full_clean()

        super(Approvisionnement, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('approvisionnement_details', args=[self.pk])


class DetailsApprovisionnement(models.Model):
    approvisionnement = models.ForeignKey(Approvisionnement, on_delete=models.PROTECT, null=True)
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.PROTECT, null=False)
    facture = models.CharField(max_length=15)
    article = models.ForeignKey('produits.Article', on_delete=models.PROTECT, null=True)
    qte = models.IntegerField()
    prix = models.DecimalField(max_digits=12, decimal_places=2)
    date_peremption = models.DateField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valeur_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    taux_creation = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    objects = models.Manager()

    @property
    def prix_total(self):
        return self.qte * self.prix

    @property
    def frais_achat(self):
        return self.frais.aggregate(
            total=Sum("montant")
        )["total"] or 0

    @property
    def cout_achat(self):
        return self.prix + self.frais_achat

    @property
    def prix_vente(self):
        prix_vente_fc, prix_vente_usd = self.article.prix_vente_devise
        if self.approvisionnement.devise == '$':
            return prix_vente_usd
        else:
            return prix_vente_fc

    @property
    def prix_vente_gros(self):
        prix_vente_gros_fc, prix_vente_gros_usd = self.article.prix_vente_gros_devise
        if self.approvisionnement.devise == '$':
            return prix_vente_gros_usd
        else:
            return prix_vente_gros_fc

    @property
    def resultat(self):
        prix_vente_fc, prix_vente_usd = self.article.prix_vente_devise
        if self.approvisionnement.devise == '$':
            return (prix_vente_usd - self.cout_achat) * self.qte
        else:
            return (prix_vente_fc - self.cout_achat) * self.qte

    @transaction.atomic
    def add(self):
        detail, created = DetailsApprovisionnement.objects.get_or_create(
            approvisionnement=self.approvisionnement,
            article=self.article,
            date_peremption=self.date_peremption,
            fournisseur=self.fournisseur,
            facture=self.facture,
            defaults={
                'qte': self.qte,
                'prix': self.prix,
            }
        )

        if not created:
            detail.qte += self.qte
            detail.save()

        return detail

    @transaction.atomic
    def update_appro(self):
        old_details = DetailsApprovisionnement.objects.get(pk=self.pk)
        old_peremption = old_details.date_peremption

        # Article et fournisseur sont verrouillés — on les réaffecte
        # depuis la BDD pour ignorer toute valeur injectée via POST.
        self.article = old_details.article
        self.fournisseur = old_details.fournisseur

        new_peremption = self.date_peremption
        new_qte = self.qte
        appro = self.approvisionnement

        # Même date de péremption ➜ simple update (article/fournisseur déjà verrouillés)
        if old_peremption == new_peremption:
            self.save()
        else:
            # Fusion uniquement avec une ligne de même source
            # (article + fournisseur + facture + nouvelle date de péremption).
            # Sans fournisseur/facture dans le filtre, on risquait de fusionner
            # deux lignes de sources différentes → perte de traçabilité.
            autre_detail = DetailsApprovisionnement.objects.filter(
                approvisionnement=appro,
                article=self.article,
                fournisseur=self.fournisseur,
                facture=self.facture,
                date_peremption=new_peremption,
            ).exclude(pk=self.pk).first()

            if autre_detail:
                autre_detail.qte += new_qte
                autre_detail.save()
                self.delete()
            else:
                self.save()

    def clean(self):
        if self.approvisionnement and self.approvisionnement.valide:
            original = DetailsApprovisionnement.objects.filter(pk=self.pk).first()
            if original:
                if self.approvisionnement.devise != original.approvisionnement.devise:
                    raise ValidationError("La devise de l'approvisionnement validé ne peut pas être modifiée.")
                if self.approvisionnement.taux != original.approvisionnement.taux:
                    raise ValidationError("Le taux de l'approvisionnement validé ne peut pas être modifié.")
                if self.taux_creation is not None and self.taux_creation != original.taux_creation:
                    raise ValidationError("Le taux de création historique ne peut pas être modifié.")
                if self.valeur_usd is not None and self.valeur_usd != original.valeur_usd:
                    raise ValidationError("La valeur USD historique ne peut pas être modifiée pour un approvisionnement validé.")

        return super().clean()

    def save(self, *args, **kwargs):
        from parametres.models import get_taux_usd_cdf
        if self.approvisionnement and self.approvisionnement.valide:
            if self.pk:
                original = DetailsApprovisionnement.objects.filter(pk=self.pk).first()
                if original:
                    self.approvisionnement = original.approvisionnement
                    self.fournisseur = original.fournisseur
                    self.article = original.article
                    self.taux_creation = original.taux_creation
                    self.valeur_usd = original.valeur_usd
        else:
            if self.taux_creation is None:
                if self.approvisionnement:
                    taux = self.approvisionnement.taux
                    if not taux:
                        date_creation = self.approvisionnement.date_creation
                        date_val = date_creation.date() if date_creation else None
                        taux = get_taux_usd_cdf(date_val)
                else:
                    taux = get_taux_usd_cdf()
                self.taux_creation = taux

            montant = Decimal(str(self.qte)) * Decimal(str(self.prix))
            if self.approvisionnement and self.approvisionnement.devise == '$':
                self.valeur_usd = montant
            else:
                self.valeur_usd = montant / self.taux_creation if self.taux_creation else Decimal('0')

        super(DetailsApprovisionnement, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('approvisionnement_details', args=[self.approvisionnement.pk])


class FraisApprovisionnement(models.Model):
    detail = models.ForeignKey(DetailsApprovisionnement, related_name="frais", on_delete=models.CASCADE)
    type_frais = models.ForeignKey(TypeFrais, on_delete=models.PROTECT)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    valeur_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    taux_creation = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    def clean(self):
        if self.pk:
            original = FraisApprovisionnement.objects.filter(pk=self.pk).first()
            if original:
                if self.taux_creation is not None and self.taux_creation != original.taux_creation:
                    raise ValidationError("Le taux de création historique ne peut pas être modifié.")
                if self.valeur_usd is not None and self.valeur_usd != original.valeur_usd:
                    raise ValidationError("La valeur USD historique d'un frais validé ne peut pas être modifiée.")

        return super().clean()

    def save(self, *args, **kwargs):
        from decimal import Decimal
        from parametres.models import get_taux_usd_cdf

        if self.pk:
            original = FraisApprovisionnement.objects.filter(pk=self.pk).first()
            if original:
                self.taux_creation = original.taux_creation

        if self.taux_creation is None:
            if self.detail and self.detail.approvisionnement:
                taux = self.detail.approvisionnement.taux
                if not taux:
                    date_creation = self.detail.approvisionnement.date_creation
                    date_val = date_creation.date() if date_creation else None
                    taux = get_taux_usd_cdf(date_val)
            else:
                taux = get_taux_usd_cdf()
            self.taux_creation = taux

        total_fee = Decimal(str(self.montant)) * Decimal(str(self.detail.qte))
        if self.detail and self.detail.approvisionnement and self.detail.approvisionnement.devise == '$':
            self.valeur_usd = total_fee
        else:
            self.valeur_usd = total_fee / self.taux_creation if self.taux_creation else Decimal('0')

        super(FraisApprovisionnement, self).save(*args, **kwargs)

