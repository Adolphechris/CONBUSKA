from django.db import models
from django.urls import reverse
from django.db.models import F, Sum
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

    def total_mouvements(self):
        if self.is_system:
            return (
                    self.mouvements()
                    .annotate(prix_total_db=F('montant') * F('detail__qte'))
                    .aggregate(total=Sum('prix_total_db'))
                    ['total'] or 0
            )

        return (
                self.mouvements()
                .annotate(prix_total_db=F('qte') * F('prix'))
                .aggregate(total=Sum('prix_total_db'))
                ['total'] or 0
        )

    def total_paiements(self):
        return self.paiements().aggregate(total=Sum('mouvement_caisse__montant'))['total'] or 0

    def solde(self):
        return self.total_mouvements() - self.total_paiements()

    @property
    def get_next_code(self):
        last_code = Fournisseur.objects.all().order_by('-code')[:1]
        try:
            code = [i.code + 1 for i in last_code][0]
        except IndexError:
            code = 2000
        return code

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code

        super(Fournisseur, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('fournisseur_details', args=[self.pk])
