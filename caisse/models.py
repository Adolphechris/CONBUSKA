from django.db import models

class Caisse(models.Model):
    nom = models.CharField(max_length=150)
    is_principal = models.BooleanField(default=False)
    objects = models.Manager()

    def __str__(self):
        return self.nom


class CaisseCourante(models.Model):
    caisse = models.ForeignKey(Caisse, on_delete=models.CASCADE, related_name='caisses')
    ouvert_par = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True,
                                   related_name='ouvertures_caisse')
    ferme_par = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='fermetures_caisse')
    date_ouverture = models.DateTimeField(auto_now_add=True)
    date_fermeture = models.DateTimeField(null=True, blank=True)
    solde_initial = models.DecimalField(max_digits=10, decimal_places=2)
    solde_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    est_ouverte = models.BooleanField(default=True)
    objects = models.Manager()

    def __str__(self):
        return f"Caisse #{self.id} - {self.date_ouverture.date()}"


class RubriqueCaisse(models.Model):
    nom = models.CharField(max_length=150)
    description = models.TextField()
    visible = models.BooleanField(default=True)
    objects = models.Manager()

    def __str__(self):
        return f"{self.nom}"


class MouvementCaisse(models.Model):
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie'),
    ]

    caisse = models.ForeignKey(CaisseCourante, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    rubrique = models.ForeignKey(RubriqueCaisse, on_delete=models.PROTECT, related_name='mouvements_rubrique')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    motif = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True, null=True)  # ex: numéro de facture
    effectue_par = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    date_mouvement = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    def __str__(self):
        return f"{self.type_mouvement} - {self.montant}"

    @property
    def solde_actuel(self):
        entrees = self.mouvements.filter(type_mouvement='ENTREE').aggregate(total=models.Sum('montant'))['total'] or 0
        sorties = self.mouvements.filter(type_mouvement='SORTIE').aggregate(total=models.Sum('montant'))['total'] or 0
        return self.solde_initial + entrees - sorties



class MouvementCaisseFournisseur(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_f')
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.CASCADE, related_name='fournisseur')


class MouvementCaisseClient(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_c')
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='client')


class MouvementCaisseCreancier(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_cr')
    creancier = models.ForeignKey('creanciers.Creancier', on_delete=models.CASCADE, related_name='creancier')


class MouvementCaisseDebiteur(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_db')
    debiteur = models.ForeignKey('creanciers.Debiteur', on_delete=models.CASCADE, related_name='debiteur')


class MouvementCaisseAgent(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_ag')
    agent = models.ForeignKey('paie.Agent', on_delete=models.CASCADE, related_name='agent')