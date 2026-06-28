"""
Signaux Django pour la synchronisation automatique avec Firestore.

Déclencheurs :
- post_save sur Article : synchronise l'article vers Firestore
- pre_delete sur Article : supprime l'article de Firestore
- post_save sur Stock : met à jour le stock_disponible dans Firestore
"""

import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from produits.models import Article, Stock

logger = logging.getLogger('ecommerce.signals')


@receiver(post_save, sender=Article)
def on_article_save(sender, instance, created, **kwargs):
    """
    Déclenche la synchronisation Firestore après modification d'un article.
    
    - Si created : création complète
    - Si updated : vérifier si est_publie a changé
    """
    try:
        from ecommerce.sync.services import FirestoreSyncService
        
        # Ne synchroniser que si l'article est publié ou vient de l'être
        if instance.est_publie:
            FirestoreSyncService.sync_article(instance)
            logger.debug(f"[SIGNAL] Article {instance.code} synchronisé (create={created})")
        else:
            # Si publié avant, maintenant dépublié → supprimer de Firestore
            if instance.derniere_sync_firestore:
                FirestoreSyncService.delete_article(str(instance.code))
                logger.debug(f"[SIGNAL] Article {instance.code} supprimé de Firestore (dépublié)")
    
    except Exception as e:
        # Ne pas bloquer le save() si la sync échoue
        logger.error(f"[SIGNAL] Erreur sync article {instance.code}: {e}")


@receiver(pre_delete, sender=Article)
def on_article_delete(sender, instance, **kwargs):
    """
    Supprime l'article de Firestore avant suppression locale.
    """
    try:
        from ecommerce.sync.services import FirestoreSyncService
        
        # Supprimer de Firestore
        FirestoreSyncService.delete_article(str(instance.code))
        logger.debug(f"[SIGNAL] Article {instance.code} supprimé de Firestore (pre_delete)")
    
    except Exception as e:
        # Ne pas bloquer la suppression locale
        logger.error(f"[SIGNAL] Erreur suppression Firestore article {instance.code}: {e}")


@receiver(post_save, sender=Stock)
def on_stock_save(sender, instance, created, **kwargs):
    """
    Met à jour le stock_disponible dans Firestore après modification d'un lot.
    """
    try:
        from ecommerce.sync.services import FirestoreSyncService
        
        # Ne synchroniser que si l'article est publié
        if instance.article.est_publie:
            FirestoreSyncService.sync_stock(instance.article)
            logger.debug(f"[SIGNAL] Stock article {instance.article.code} synchronisé")
    
    except Exception as e:
        # Ne pas bloquer le save() si la sync échoue
        logger.error(f"[SIGNAL] Erreur sync stock article {instance.article.code}: {e}")