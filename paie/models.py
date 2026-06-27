"""
paie/models.py

Modèles du module paie.
Structure uniquement. Aucune logique métier.
"""

from django.db import models
from django.urls import reverse


class TypeContrat(models.TextChoices):
    CDI        = 'CDI',        'CDI'
    CDD        = 'CDD',        'CDD'
    CONSULTANT = 'CONSULTANT', 'Consultant'


class TypeLigne(models.TextChoices):
    GAIN    = 'GAIN',    'Gain'     # s'ajoute au net à payer
    RETENUE = 'RETENUE', 'Retenue'  # se soustrait du net à payer


class Agent(models.Model):
    matricule         = models.IntegerField(unique=True)
    nom               = models.CharField(max_length=150, unique=True)
    date_naissance    = models.DateField()
    date_engagement   = models.DateField()
    photo             = models.ImageField(upload_to='agents/', blank=True)
    email             = models.EmailField(unique=True, blank=True, null=True)
    adresse           = models.CharField(max_length=150)
    telephone         = models.CharField(max_length=50)
    ville             = models.CharField(max_length=50)
    poste             = models.CharField(max_length=100, blank=True)
    departement       = models.CharField(max_length=100, blank=True)
    type_contrat      = models.CharField(
        max_length=20,
        choices=TypeContrat.choices,
        default=TypeContrat.CDI,
    )
    salaire           = models.DecimalField(max_digits=12, decimal_places=2)
    actif             = models.BooleanField(default=True)
    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        ordering            = ['nom']
        verbose_name        = 'Agent'
        verbose_name_plural = 'Agents'

    def __str__(self) -> str:
        return self.nom

    def get_absolute_url(self) -> str:
        return reverse('agent_details', args=[self.pk])


class Paie(models.Model):
    """
    Bulletin de paie mensuel d'un agent.

    Toutes les valeurs calculées sont des snapshots pris au moment
    de la création — indépendants des modifications ultérieures
    du salaire ou des mouvements caisse.

    Formule :
        salaire_brut   = salaire_base × (jp / jap)
        total_primes   = Σ LignePaie[type=GAIN]
        total_retenues = Σ LignePaie[type=RETENUE]
        net_a_payer    = salaire_brut + total_primes − total_retenues
    """

    mois  = models.DateField()   # toujours normalisé au 1er du mois
    agent = models.ForeignKey(
        Agent,
        related_name='paies',
        on_delete=models.PROTECT,
    )

    # ── Snapshot de présence ──────────────────────────────────────────
    salaire_base = models.DecimalField(max_digits=12, decimal_places=2)
    jap          = models.IntegerField(default=26)   # jours ouvrables du mois
    jp           = models.IntegerField(default=26)   # jours payés (jap − absence)
    absence      = models.IntegerField(default=0)

    # ── Résultats calculés (snapshot immuable après validation) ───────
    salaire_brut   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_primes   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_retenues = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_a_payer    = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ── Dual currency ─────────────────────────────────────────────────
    taux_creation = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True,
                                        help_text="Taux de change historique au moment de la création")
    valeur_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True,
                                     help_text="Valeur USD du net à payer (historique, immuable)")

    # ── Workflow ──────────────────────────────────────────────────────
    valide      = models.BooleanField(default=False)
    cree_par    = models.ForeignKey(
        'users.CustomUser',
        related_name='paie_cree_par',
        on_delete=models.PROTECT,
    )
    modifie_par = models.ForeignKey(
        'users.CustomUser',
        related_name='paie_modifie_par',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        unique_together     = [('agent', 'mois')]
        ordering            = ['-mois', 'agent__nom']
        verbose_name        = 'Paie'
        verbose_name_plural = 'Paies'

    def __str__(self) -> str:
        return f"{self.agent} — {self.mois.strftime('%m/%Y')}"

    def get_absolute_url(self) -> str:
        return reverse('paie_agent_details', args=[self.pk, self.agent_id])


class LignePaie(models.Model):
    """
    Ligne de détail d'un bulletin de paie.

    Chaque rubrique (prime, retenue, avance…) est une ligne distincte.
    Les lignes sont des snapshots — elles persistent même si la Paie
    est supprimée (on_delete=PROTECT : supprimer les lignes d'abord via service).

    Extensibilité : pour ajouter CNSS ou IPR, créer une LignePaie
    supplémentaire avec type_ligne=RETENUE et le libellé approprié.
    Le net_a_payer de Paie est recalculé automatiquement depuis ces lignes.
    """

    paie       = models.ForeignKey(
        Paie,
        related_name='lignes',
        on_delete=models.PROTECT,
    )
    libelle    = models.CharField(max_length=150)
    type_ligne = models.CharField(max_length=10, choices=TypeLigne.choices)
    montant    = models.DecimalField(max_digits=12, decimal_places=2)
    ordre      = models.PositiveSmallIntegerField(default=0)
    valeur_usd = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True,
                                     help_text="Valeur USD historique de cette ligne (immuable)")
    taux_creation = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True,
                                        help_text="Taux de change au moment de la création")

    objects = models.Manager()

    class Meta:
        ordering            = ['ordre', 'id']
        verbose_name        = 'Ligne de paie'
        verbose_name_plural = 'Lignes de paie'

    def __str__(self) -> str:
        signe = '+' if self.type_ligne == TypeLigne.GAIN else '−'
        return f"{signe} {self.libelle} : {self.montant}"
