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
    solde_initial = models.DecimalField(max_digits=18, decimal_places=2)
    solde_final = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
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


class SousRubriqueCaisse(models.Model):
    rubrique = models.ForeignKey(RubriqueCaisse, on_delete=models.CASCADE, related_name='sous_rubriques')
    nom = models.CharField(max_length=45)
    description = models.TextField()
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
    sous_rubrique = models.ForeignKey(SousRubriqueCaisse, on_delete=models.PROTECT, null=True, blank=True)
    caisse_destination = models.ForeignKey(
        'Caisse', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transferts_sortants',
    )
    mouvement_transfert_source = models.OneToOneField(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='mouvement_transfert_miroir',
    )
    montant = models.DecimalField(max_digits=18, decimal_places=2)
    motif = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True, null=True)  # ex: numéro de facture
    effectue_par = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    date_mouvement = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        ordering = ['date_mouvement']
        indexes = [
            models.Index(fields=['date_mouvement']),
            models.Index(fields=['type_mouvement']),
        ]

    def __str__(self):
        return f"{self.type_mouvement} - {self.montant}"

    @property
    def badge_entite(self):
        """Returns the linked entity name for the rubrique badge in the table.

        Uses prefetch caches when the queryset was built with prefetch_related;
        falls back to individual queries otherwise.
        """
        # Transfert caisse → caisse de destination (FK persisté)
        if self.caisse_destination_id:
            return str(self.caisse_destination)

        # Sous-rubrique directe (charges exploitation / personnelles via le form)
        if self.sous_rubrique_id:
            return str(self.sous_rubrique)

        # Tables de liaison tiers
        for related, field in (
            ("mouvements_caisse_f", "fournisseur"),
            ("mouvements_caisse_c", "client"),
            ("mouvements_caisse_cr", "creancier"),
            ("mouvements_caisse_db", "debiteur"),
            ("mouvements_caisse_ag", "agent"),
            ("mouvements_caisse_ce", "sous_rubrique"),
            ("mouvements_caisse_cp", "sous_rubrique"),
        ):
            qs = getattr(self, related).all()
            if qs:
                return str(getattr(qs[0], field))

        return None

    @property
    def solde_actuel(self):
        entrees = self.mouvements.filter(type_mouvement='ENTREE').aggregate(total=models.Sum('montant'))['total'] or 0
        sorties = self.mouvements.filter(type_mouvement='SORTIE').aggregate(total=models.Sum('montant'))['total'] or 0
        return self.solde_initial + entrees - sorties


class MouvementCaisseFournisseur(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_f')
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.CASCADE, related_name='fournisseur')
    objects = models.Manager()


class MouvementCaisseClient(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_c')
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='client')
    objects = models.Manager()


class MouvementCaisseCreancier(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_cr')
    creancier = models.ForeignKey('creanciers.Creancier', on_delete=models.CASCADE, related_name='creancier')
    objects = models.Manager()


class MouvementCaisseDebiteur(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_db')
    debiteur = models.ForeignKey('creanciers.Debiteur', on_delete=models.CASCADE, related_name='debiteur')
    objects = models.Manager()


class MouvementCaisseAgent(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_ag')
    agent = models.ForeignKey('paie.Agent', on_delete=models.CASCADE, related_name='agent')
    objects = models.Manager()


class MouvementCaisseChargesExploitation(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_ce')
    sous_rubrique = models.ForeignKey(SousRubriqueCaisse, on_delete=models.CASCADE, related_name='sous_rubrique_ce')
    objects = models.Manager()

class MouvementCaisseChargesPersonnelles(models.Model):
    mouvement_caisse = models.ForeignKey(MouvementCaisse, on_delete=models.CASCADE, related_name='mouvements_caisse_cp')
    sous_rubrique = models.ForeignKey(SousRubriqueCaisse, on_delete=models.CASCADE, related_name='sous_rubrique_cp')
    objects = models.Manager()
