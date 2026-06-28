"""
Modèles e-commerce pour la boutique en ligne.

Gère :
- Images des articles (ImageArticle)
- Logs e-commerce (EcommerceLog)
- Configuration e-commerce (EcommerceConfig)
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone

User = get_user_model()


class ImageArticle(models.Model):
    """
    Stocke les images des articles avec leurs versions transformées.
    L'image originale est conservée, les versions WebP sont générées.
    """
    article = models.ForeignKey(
        'produits.Article',
        on_delete=models.CASCADE,
        related_name='images'
    )
    image_originale = models.ImageField(upload_to='articles/originaux/')
    image_webp_600 = models.ImageField(upload_to='articles/webp/600x600/', blank=True)
    image_webp_150 = models.ImageField(upload_to='articles/webp/150x150/', blank=True)
    est_principale = models.BooleanField(default=False)
    ordre = models.IntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-est_principale', 'ordre', 'date_creation']
        verbose_name = "Image d'article"
        verbose_name_plural = "Images d'articles"
    
    def __str__(self):
        return f"Image {self.article.designation}"


class EcommerceLog(models.Model):
    """Log des opérations e-commerce."""
    
    EVENEMENTS = (
        ('sync_article', 'Synchronisation article'),
        ('sync_stock', 'Synchronisation stock'),
        ('import_commande', 'Import commande'),
        ('erreur_sync', 'Erreur synchronisation'),
        ('erreur_import', 'Erreur import'),
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    evenement = models.CharField(max_length=50, choices=EVENEMENTS)
    article_code = models.CharField(max_length=50, blank=True, null=True)
    commande_id = models.CharField(max_length=100, blank=True, null=True)
    success = models.BooleanField()
    message = models.TextField(blank=True)
    duree_ms = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['evenement', 'timestamp']),
            models.Index(fields=['commande_id']),
        ]
    
    def __str__(self):
        return f"[{self.timestamp}] {self.evenement} - {'OK' if self.success else 'ERREUR'}"


class EcommerceConfig(models.Model):
    """Configuration globale du module e-commerce."""
    
    cle = models.CharField(max_length=100, unique=True)
    valeur = models.TextField()
    description = models.TextField(blank=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuration e-commerce"
        verbose_name_plural = "Configurations e-commerce"
    
    def __str__(self):
        return self.cle
    
    @classmethod
    def get_config(cls, cle: str, default: str = '') -> str:
        """Récupère une valeur de configuration."""
        try:
            config = cls.objects.get(cle=cle)
            return config.valeur
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_config(cls, cle: str, valeur: str, description: str = '') -> None:
        """Définit une valeur de configuration."""
        config, created = cls.objects.get_or_create(
            cle=cle,
            defaults={'valeur': valeur, 'description': description}
        )
        if not created:
            config.valeur = valeur
            config.save()


class SyncQueue(models.Model):
    """
    File d'attente des modifications en attente de synchronisation.
    Utilisée quand Firestore est indisponible.
    """

    STATUT_CHOICES = (
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    )

    article = models.ForeignKey('produits.Article', on_delete=models.CASCADE)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='pending')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    tentatives = models.IntegerField(default=0)
    erreur = models.TextField(blank=True)

    class Meta:
        ordering = ['date_creation']
        verbose_name = "File de synchronisation"
        verbose_name_plural = "File de synchronisation"

    def __str__(self):
        return f"Sync {self.article.designation} - {self.statut}"