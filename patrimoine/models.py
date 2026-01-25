from django.db import models
from caisse.models import Caisse
from approvisionnements.models import Approvisionnement


class SnapshotJournalier(models.Model):
    date = models.DateField()
    caisse = models.ForeignKey(Caisse, on_delete=models.PROTECT)

    total_entrees = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_sorties = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    solde_ouverture = models.DecimalField(max_digits=14, decimal_places=2)
    solde_fermeture = models.DecimalField(max_digits=14, decimal_places=2)

    est_cloture = models.BooleanField(default=False)

    class Meta:
        unique_together = ('date', 'caisse')


class SnapshotMensuel(models.Model):
    annee = models.IntegerField()
    mois = models.IntegerField()
    caisse = models.ForeignKey(Caisse, on_delete=models.PROTECT)

    total_entrees = models.DecimalField(max_digits=16, decimal_places=2)
    total_sorties = models.DecimalField(max_digits=16, decimal_places=2)
    solde_fin_mois = models.DecimalField(max_digits=16, decimal_places=2)

    est_cloture = models.BooleanField(default=False)

    class Meta:
        unique_together = ('annee', 'mois', 'caisse')


class ResultatApprovisionnementSnapshot(models.Model):
    approvisionnement = models.OneToOneField(Approvisionnement, on_delete=models.PROTECT)
    date = models.DateField(db_index=True)
    devise = models.CharField(max_length=2)
    taux = models.DecimalField(max_digits=6, decimal_places=2)
    resultat_brut = models.DecimalField(max_digits=14, decimal_places=2)
    cout_achat = models.DecimalField(max_digits=14, decimal_places=2)
    frais_achat = models.DecimalField(max_digits=14, decimal_places=2)
    chiffre_affaires = models.DecimalField(max_digits=14, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)


class ResultatJournalier(models.Model):
    date = models.DateField(unique=True)
    resultat_brut = models.DecimalField(max_digits=14, decimal_places=2)
    chiffre_affaires = models.DecimalField(max_digits=14, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)


class ResultatMensuel(models.Model):
    mois = models.IntegerField()
    annee = models.IntegerField()
    resultat_brut = models.DecimalField(max_digits=14, decimal_places=2)
    chiffre_affaires = models.DecimalField(max_digits=14, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mois', 'annee')
