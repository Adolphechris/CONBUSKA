from django.db import models, transaction
from django.urls import reverse
from django.db.models import F, Sum, Max
from approvisionnements.models import DetailsApprovisionnement, TypeFrais, FraisApprovisionnement
from caisse.models import MouvementCaisseFournisseur


class Fournisseur(models.Model):
    code = models.IntegerField(unique=True, blank=False)
    photo = models.ImageField(upload_to='fournisseurs/', blank=True)
    nom = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    adresse = models.CharField(max_length=150)
    telephone = models.CharField(max_length=150)
    ville = models.CharField(max_length=30)
    pays = models.CharField(max_length=30)
    tuteur = models.CharField(max_length=30)
    rccm = models.CharField(max_length=30)
    id_nat = models.CharField(max_length=30)
    impot = models.CharField(max_length=30)
    tva = models.CharField(max_length=30)
    is_system = models.BooleanField(default=False)
    actif = models.BooleanField(default=True)
    type_frais = models.ForeignKey(TypeFrais, null=True, blank=True, on_delete=models.PROTECT)

    objects = models.Manager()

    def __str__(self):
        return self.nom

    def mouvements(self):
        if self.is_system:
            return FraisApprovisionnement.objects.filter(type_frais=self.type_frais)
        return DetailsApprovisionnement.objects.filter(fournisseur=self)

    def paiements(self):
        return MouvementCaisseFournisseur.objects.filter(fournisseur=self)

    def total_mouvements_usd(self):
        from decimal import Decimal
        return self.mouvements().aggregate(total=Sum('valeur_usd'))['total'] or Decimal('0')

    def total_paiements_usd(self):
        from decimal import Decimal
        return self.paiements().aggregate(total=Sum('valeur_usd'))['total'] or Decimal('0')

    def solde_usd(self):
        return self.total_mouvements_usd() - self.total_paiements_usd()

    def solde_fc(self):
        return self.total_mouvements() - self.total_paiements()

    def total_mouvements(self):
        from django.db.models import ExpressionWrapper, DecimalField
        return (
            self.mouvements()
            .aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('valeur_usd') * F('taux_creation'),
                        output_field=DecimalField(max_digits=18, decimal_places=4)
                    )
                )
            )['total']
            or 0
        )

    def total_paiements(self):
        return self.paiements().aggregate(total=Sum('mouvement_caisse__montant'))['total'] or 0

    def solde(self):
        return self.solde_usd()

    @property
    def get_next_code(self):
        with transaction.atomic():
            last_code = Fournisseur.objects.select_for_update().aggregate(mcode=Max("code"))["mcode"]
        return (last_code + 1) if last_code else 2000

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code

        super(Fournisseur, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('fournisseur_details', args=[self.pk])
