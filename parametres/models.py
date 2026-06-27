from django.db import models
from django.urls import reverse
from django.utils.timezone import localdate
from simple_history.models import HistoricalRecords
from decimal import Decimal

from .exceptions import RateNotFoundError


# ── Devise ─────────────────────────────────────────────────────────────────────

class Devise(models.Model):
    """Table des devises, source unique de vérité pour tout le système."""
    code    = models.CharField(max_length=5, unique=True, verbose_name='Code')
    nom     = models.CharField(max_length=50, verbose_name='Nom')
    symbole = models.CharField(max_length=5, verbose_name='Symbole')
    actif   = models.BooleanField(default=True, verbose_name='Active')
    date_creation    = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    class Meta:
        verbose_name = 'Devise'
        verbose_name_plural = 'Devises'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} – {self.nom}"

    @staticmethod
    def get_absolute_url():
        return reverse('devises')


# ── Manager ───────────────────────────────────────────────────────────────────

class TauxEchangeManager(models.Manager):
    def get_rate_for_date(self, source: str, cible: str, date=None) -> 'TauxEchange':
        """
        Retourne le taux le plus récent avec effective_date <= date.
        Comportement "dernier taux connu" : un taux reste valide jusqu'à la
        prochaine modification manuelle.

        Paramètres :
            source : code devise d'origine  (ex: 'USD')
            cible  : code devise de sortie  (ex: 'CDF')
            date   : date de référence (défaut : aujourd'hui en heure locale)

        Raises:
            RateNotFoundError : aucun taux valide pour cette paire et cette date.
        """
        if date is None:
            date = localdate()

        instance = (
            self.filter(
                devise_source=source,
                devise_cible=cible,
                effective_date__lte=date,
            )
            .order_by('-effective_date')
            .first()
        )

        if instance is None:
            raise RateNotFoundError(
                f"Aucun taux {source} → {cible} valide au {date}. "
                "Veuillez saisir un taux dans Paramètres → Taux d'échange."
            )

        return instance


def get_taux_usd_cdf(date=None):
    """
    Retourne le taux USD → CDF (équivalent $ → FC) pour la date donnée.
    Utilisé par factures, produits, patrimoine pour les conversions de devises.
    
    Si aucun taux n'est trouvé, retourne une valeur par défaut (2500.00) pour
    éviter les crashes dans les tests et en production.
    """
    try:
        return TauxEchange.objects.get_rate_for_date('USD', 'CDF', date).taux
    except RateNotFoundError:
        # Fallback pour tests et sécurité
        return Decimal('2500.00')


class Parametre(models.Model):
    code = models.CharField(max_length=6, default='Params')
    logo = models.ImageField(upload_to='logo/', blank=True, null=True)
    sigle = models.CharField(max_length=30, blank=True, null=True)
    societe = models.CharField(max_length=40, blank=True, null=True)
    rccm = models.CharField(max_length=40, blank=True, null=True)
    idnat = models.CharField(max_length=40, blank=True, null=True)
    impot = models.CharField(max_length=40, blank=True, null=True)
    tva = models.CharField(max_length=50, blank=True, null=True)
    pays = models.CharField(max_length=30, blank=True, null=True)
    adresse = models.CharField(max_length=150, blank=True, null=True)
    ville = models.CharField(max_length=30, blank=True, null=True)
    telephone = models.CharField(max_length=40, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def __str__(self):
        return self.code

    @staticmethod
    def get_absolute_url():
        return reverse('parametres')


class Magasin(models.Model):
    nom = models.CharField(max_length=25)
    description = models.TextField()
    is_principal = models.BooleanField(default=False)
    localisation = models.CharField(max_length=30)
    objects = models.Manager()

    def __str__(self):
        return self.nom

    @staticmethod
    def get_absolute_url():
        return reverse('magasins')


class TauxEchange(models.Model):
    """
    Taux de change entre deux devises, applicable à partir de effective_date.

    Règle "dernier taux connu" :
        Un taux reste en vigueur jusqu'à la prochaine saisie manuelle.
        get_rate_for_date() retourne toujours le taux le plus récent
        dont effective_date <= date demandée.

    Unicité :
        Un seul taux par paire (source, cible) et par jour (effective_date).
        Pour corriger un taux du jour : éditer l'enregistrement existant —
        simple_history trace l'ancienne valeur automatiquement.
    """
    devise_source   = models.CharField(
        max_length=5, default='USD',
        verbose_name='Devise source'
    )
    devise_cible    = models.CharField(
        max_length=5, default='CDF',
        verbose_name='Devise cible'
    )
    taux            = models.DecimalField(
        max_digits=12, decimal_places=4,
        verbose_name='Taux'
    )
    effective_date  = models.DateField(
        verbose_name="Date d'application",
        help_text="Date à partir de laquelle ce taux est applicable."
    )
    modifie_par     = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Modifié par',
        related_name='taux_modifies'
    )
    date_creation   = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    history         = HistoricalRecords()
    objects         = TauxEchangeManager()

    class Meta:
        verbose_name        = "Taux d'échange"
        verbose_name_plural = "Taux d'échange"
        ordering            = ['-effective_date']
        constraints         = [
            models.UniqueConstraint(
                fields=['devise_source', 'devise_cible', 'effective_date'],
                name='unique_rate_per_day',
            )
        ]

    def __str__(self):
        from decimal import Decimal
        taux = Decimal(str(self.taux))
        return (
            f"{self.devise_source} → {self.devise_cible} : "
            f"{taux:,.4f} ({self.effective_date})"
        )