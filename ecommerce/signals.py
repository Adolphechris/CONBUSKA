"""
Signaux Django pour la synchronisation automatique avec Firestore.
Ces signaux sont enregistrés automatiquement au démarrage de l'application
via ecommerce/apps.py -> ready().
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

# Import différé pour éviter les imports circulaires
# Les modèles seront importés dans les signaux eux-mêmes


@receiver(post_save, sender='produits.Article')
def on_article_save(sender, instance, created, **kwargs):
    """
    Déclenche la synchronisation Firestore après modification d'un article.
    
    - Si est_publie = True : synchronise l'article vers Firestore
    - Si est_publie = False et article était publié avant : supprime de Firestore
    
    La synchronisation se fait de manière asynchrone (ne bloque pas le save).
    Les erreurs sont loggées mais n'interrompent pas le système local.
    """
    try:
        if instance.est_publie:
            # Synchroniser l'article vers Firestore (temps réel)
            from ecommerce.sync.services import FirestoreSyncService
            FirestoreSyncService.sync_article(instance)
        else:
            # Vérifier si l'article était publié avant → supprimer de Firestore
            if instance.derniere_sync_firestore:
                from ecommerce.sync.services import FirestoreSyncService
                FirestoreSyncService.delete_article(str(instance.code))
    except Exception:
        # Ne jamais bloquer le système local à cause de la sync
        pass


@receiver(pre_delete, sender='produits.Article')
def on_article_delete(sender, instance, **kwargs):
    """
    Supprime l'article de Firestore avant suppression locale.
    
    Se déclenche automatiquement quand un article est supprimé.
    Supprime à la fois le document Firestore et les images Storage.
    """
    try:
        from ecommerce.sync.services import FirestoreSyncService
        if instance.est_publie or instance.derniere_sync_firestore:
            FirestoreSyncService.delete_article(str(instance.code))
    except Exception:
        pass


@receiver(post_save, sender='produits.Stock')
def on_stock_save(sender, instance, created, **kwargs):
    """
    Met à jour le stock_disponible dans Firestore après modification d'un lot.
    
    Se déclenche quand un lot de stock est ajouté, modifié ou supprimé.
    Re-synchronise l'article parent si celui-ci est publié.
    """
    try:
        from ecommerce.sync.services import FirestoreSyncService
        article = instance.article
        if article.est_publie:
            # Sync seulement le stock (pas toute l'image)
            FirestoreSyncService.sync_article(article)
    except Exception:
        pass
