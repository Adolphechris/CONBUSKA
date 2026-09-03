from django.db import models
from django.conf import settings
from caisse.models import Caisse
from approvisionnements.models import Approvisionnement


class SnapshotJournalier(models.Model):
    date = models.DateField()
    caisse = models.ForeignKey(Caisse, on_delete=models.PROTECT)

    total_entrees = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_sorties = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    solde_ouverture = models.DecimalField(max_digits=14, decimal_places=2)
    solde_fermeture = models.DecimalField(max_digits=14, decimal_places=2)

    # Dual currency: valeur USD du solde de fermeture
    solde_fermeture_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

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

    # Dual currency: valeurs USD
    taux_mensuel = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    solde_fin_mois_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

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

    # Dual currency: valeurs USD
    resultat_brut_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    cout_achat_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    frais_achat_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    chiffre_affaires_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)


class ResultatJournalier(models.Model):
    date = models.DateField(unique=True)
    resultat_brut = models.DecimalField(max_digits=14, decimal_places=2)
    chiffre_affaires = models.DecimalField(max_digits=14, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)

    # Dual currency: valeurs USD
    resultat_brut_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    chiffre_affaires_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)


class ResultatMensuel(models.Model):
    mois = models.IntegerField()
    annee = models.IntegerField()
    resultat_brut = models.DecimalField(max_digits=14, decimal_places=2)
    chiffre_affaires = models.DecimalField(max_digits=14, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)

    # Dual currency: valeurs USD
    resultat_brut_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    chiffre_affaires_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    class Meta:
        unique_together = ('mois', 'annee')


class FondsRoulementSnapshot(models.Model):
    date = models.DateField(unique=True, db_index=True)
    fr_initial = models.DecimalField(max_digits=16, decimal_places=2)
    ej = models.DecimalField(max_digits=16, decimal_places=2)
    sj = models.DecimalField(max_digits=16, decimal_places=2)
    fr_final = models.DecimalField(max_digits=16, decimal_places=2)
    fr_calcule = models.DecimalField(max_digits=16, decimal_places=2, help_text="FR recalculé pour vérification")
    ecart = models.DecimalField(max_digits=16, decimal_places=2)

    # Dual currency: valeurs USD historiques (immuables après création)
    taux_jour = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True,
                                    help_text="Taux USD/FC du jour")
    fr_initial_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    ej_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    sj_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    fr_final_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # Validation métier
    valide = models.BooleanField(default=False)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="validations_fr",
    )
    valide_le = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        statut = "✓" if self.valide else "~"
        return f"[{statut}] FR {self.date} — {self.fr_final} FC"
