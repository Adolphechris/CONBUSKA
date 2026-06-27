"""
Service principal de synchronisation Conbuska → Firestore.

Gère la logique métier de synchronisation des articles :
- Push des articles modifiés vers Firestore
- Suppression des articles dépubliés/supprimés
- Upload des images
- Détection des changements (incrémentale)
- Retry avec backoff exponentiel
- Logging et statistiques
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from django.db.models import F, Q
from django.utils import timezone

from ecommerce.exceptions import (
    FirebaseConnectionError,
    ImageTransformationError,
    SyncError,
)
from ecommerce.sync.serializers import FirestoreArticleSerializer
from ecommerce.sync.storage import FirebaseStorageService

logger = logging.getLogger('ecommerce.sync')

# Constantes
MAX_RETRIES = 3
BACKOFF_DELAYS = [2, 4, 8]  # secondes
BATCH_MAX_SIZE = 500

# Statistiques globales (réinitialisées au démarrage)
_sync_stats = {
    'derniere_synchro': None,
    'articles_synchronises': 0,
    'articles_supprimes': 0,
    'erreurs': [],
    'dernieres_erreurs': [],
}


class FirestoreSyncService:
    """
    Service de synchronisation des articles Conbuska → Firestore.

    Points d'entrée principaux :
    - sync_article() : Synchronisation temps réel d'un article
    - sync_all()     : Synchronisation par lots (périodique)
    - delete_article(): Suppression d'un article dans Firestore
    - get_sync_stats(): Retourne les statistiques de synchronisation
    """

    # ── API publique ─────────────────────────────────────────────────

    @classmethod
    def sync_article(cls, article, force: bool = False) -> bool:
        """
        Synchronise un article unique vers Firestore.

        Appelé par les signaux Django (post_save) pour la sync temps réel.
        Utilise merge=True pour ne pas écraser les champs non modifiés.

        Args:
            article: Instance du modèle Article
            force: Si True, force la sync même si l'article n'est pas modifié

        Returns:
            bool: True si la synchronisation a réussi

        Raises:
            SyncError: Si l'article ne peut pas être synchronisé
        """
        try:
            # Vérifier si l'article est publiable
            if not cls._is_article_publishable(article):
                # Si l'article était publié avant, le supprimer
                if article.derniere_sync_firestore:
                    cls.delete_article(str(article.code))
                return False

            # Uploader l'image d'abord
            image_url = None
            try:
                image_url = FirebaseStorageService.upload_article_image(
                    article, force=force
                )
            except ImageTransformationError as e:
                logger.warning(
                    f"Article {article.code} : upload image ignoré ({e})"
                )

            # Sérialiser l'article
            doc = FirestoreArticleSerializer.serialize(article, image_url=image_url)
            doc_id = FirestoreArticleSerializer.get_document_id(article)

            # Écrire dans Firestore (avec retry)
            def _write():
                db = cls._get_firestore_client()
                db.collection('articles_publics').document(doc_id).set(
                    doc, merge=True
                )

            cls._execute_with_retry(_write, f"sync article {doc_id}")

            # Mettre à jour la date de sync
            cls._update_sync_date(article)

            # Mettre à jour les statistiques
            _sync_stats['articles_synchronises'] += 1
            _sync_stats['derniere_synchro'] = timezone.now()

            logger.info(
                f"[SYNC] {timezone.now().isoformat()} - PUSH - "
                f"{doc_id} - SUCCESS"
            )
            return True

        except Exception as e:
            error_msg = f"Erreur sync article {article.code}: {e}"
            logger.error(f"[SYNC] {timezone.now().isoformat()} - PUSH - "
                         f"{article.code} - ERROR - {error_msg}")
            cls._add_error(error_msg)
            return False

    @classmethod
    def delete_article(cls, article_code: str) -> bool:
        """
        Supprime un article de Firestore et ses images du Storage.

        Appelé quand :
        - L'article est supprimé localement (signal pre_delete)
        - est_publie passe à false (signal post_save)

        Args:
            article_code: Code de l'article (ex: "ART001")

        Returns:
            bool: True si la suppression a réussi
        """
        try:
            # Supprimer du Storage
            FirebaseStorageService.delete_article_images(article_code)

            # Supprimer de Firestore
            def _delete():
                db = cls._get_firestore_client()
                db.collection('articles_publics').document(article_code).delete()

            cls._execute_with_retry(_delete, f"delete article {article_code}")

            _sync_stats['articles_supprimes'] += 1

            logger.info(
                f"[SYNC] {timezone.now().isoformat()} - DELETE - "
                f"{article_code} - SUCCESS"
            )
            return True

        except Exception as e:
            error_msg = f"Erreur suppression article {article_code}: {e}"
            logger.error(f"[SYNC] {timezone.now().isoformat()} - DELETE - "
                         f"{article_code} - ERROR - {error_msg}")
            cls._add_error(error_msg)
            return False

    @classmethod
    def sync_all(cls, force: bool = False) -> Tuple[int, int]:
        """
        Synchronise tous les articles publiés vers Firestore.

        Utilisé par :
        - La tâche planifiée (toutes les 5 minutes)
        - La commande management `sync_firestore`

        Utilise des batches Firestore (max 500 opérations) pour les performances.

        Args:
            force: Si True, synchronise tous les articles (pas d'incrémental)

        Returns:
            Tuple[int, int]: (nombre de succès, nombre d'échecs)
        """
        from produits.models import Article

        # Articles à synchroniser
        if force:
            articles = Article.objects.filter(est_publie=True)
        else:
            # Sync incrémentale : articles modifiés depuis la dernière sync
            articles = cls._get_articles_to_sync()

        # Articles à supprimer (dépubliés)
        articles_a_supprimer = Article.objects.filter(
            est_publie=False,
            derniere_sync_firestore__isnull=False,
        )

        # Supprimer les articles dépubliés
        for article in articles_a_supprimer:
            cls.delete_article(str(article.code))

        if not articles.exists():
            logger.debug("[SYNC] Aucun article à synchroniser")
            return (0, 0)

        # Synchroniser par lots
        success = 0
        errors = 0
        batch = []

        for article in articles:
            try:
                # Upload image
                image_url = None
                try:
                    image_url = FirebaseStorageService.upload_article_image(article)
                except ImageTransformationError:
                    pass

                # Sérialiser
                doc = FirestoreArticleSerializer.serialize(article, image_url=image_url)
                doc_id = FirestoreArticleSerializer.get_document_id(article)

                batch.append((doc_id, doc))
                success += 1

                # Vider le batch si taille max atteinte
                if len(batch) >= BATCH_MAX_SIZE:
                    cls._write_batch(batch)
                    batch = []

            except SyncError as e:
                logger.warning(f"Article {article.code} ignoré : {e}")
                errors += 1
                continue

        # Vider le dernier batch
        if batch:
            cls._write_batch(batch)

        # Mettre à jour les dates de sync
        for article in articles:
            cls._update_sync_date(article)

        _sync_stats['derniere_synchro'] = timezone.now()

        logger.info(
            f"[SYNC] Sync complète : {success} succès, {errors} échecs"
        )
        return (success, errors)

    @classmethod
    def get_sync_stats(cls) -> dict:
        """
        Retourne les statistiques de synchronisation.

        Returns:
            dict: {
                'derniere_synchro': timestamp ou None,
                'articles_synchronises': int,
                'articles_supprimes': int,
                'dernieres_erreurs': list[str] (10 max)
            }
        """
        return {
            'derniere_synchro': _sync_stats['derniere_synchro'],
            'articles_synchronises': _sync_stats['articles_synchronises'],
            'articles_supprimes': _sync_stats['articles_supprimes'],
            'dernieres_erreurs': _sync_stats['dernieres_erreurs'][-10:],
        }

    # ── Méthodes internes ────────────────────────────────────────────

    @staticmethod
    def _is_article_publishable(article) -> bool:
        """
        Vérifie si un article peut être publié en ligne.

        Critères :
        - est_publie = True
        - article actif

        Args:
            article: Instance du modèle Article

        Returns:
            bool: True si l'article est publiable
        """
        if not article.est_publie:
            return False
        if not article.actif:
            return False
        return True

    @staticmethod
    def _get_articles_to_sync():
        """
        Récupère les articles modifiés depuis la dernière synchronisation.

        Utilise le champ derniere_sync_firestore pour détecter
        les modifications incrémentales.

        Returns:
            QuerySet: Articles publiés et modifiés
        """
        from produits.models import Article

        return Article.objects.filter(
            est_publie=True,
        ).filter(
            Q(derniere_sync_firestore__isnull=True) |
            Q(derniere_sync_firestore__lt=F('date_modification'))
        )

    @classmethod
    def _write_batch(cls, batch: List[Tuple[str, dict]]) -> None:
        """
        Écrit un batch de documents dans Firestore.

        Args:
            batch: Liste de (document_id, document_data)

        Raises:
            FirebaseConnectionError: Si l'écriture échoue
        """
        def _write():
            db = cls._get_firestore_client()
            firestore_batch = db.batch()

            for doc_id, doc_data in batch:
                doc_ref = db.collection('articles_publics').document(doc_id)
                firestore_batch.set(doc_ref, doc_data, merge=True)

            firestore_batch.commit()

        cls._execute_with_retry(
            _write, f"batch write ({len(batch)} documents)"
        )

    @staticmethod
    def _update_sync_date(article) -> None:
        """
        Met à jour la date de dernière synchronisation.

        Args:
            article: Instance du modèle Article
        """
        from produits.models import Article

        Article.objects.filter(pk=article.pk).update(
            derniere_sync_firestore=timezone.now()
        )

    @staticmethod
    def _get_firestore_client():
        """
        Récupère le client Firestore.

        Returns:
            firestore.Client: Client Firestore

        Raises:
            FirebaseConnectionError: Si Firebase n'est pas initialisé
        """
        try:
            import firebase_admin
            from firebase_admin import firestore

            if not firebase_admin._apps:
                # Initialisation différée (les credentials sont dans settings)
                from django.conf import settings
                cred_path = getattr(settings, 'FIREBASE_CREDENTIALS', None)
                if cred_path:
                    cred = firebase_admin.credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': getattr(
                            settings, 'FIREBASE_STORAGE_BUCKET', None
                        ),
                    })
                else:
                    # Mode émulateur ou développement
                    firebase_admin.initialize_app()

            return firestore.client()

        except Exception as e:
            raise FirebaseConnectionError(
                f"Impossible de se connecter à Firestore: {e}"
            ) from e

    @staticmethod
    def _execute_with_retry(func, operation_name: str) -> None:
        """
        Exécute une fonction avec retry et backoff exponentiel.

        Args:
            func: Fonction à exécuter
            operation_name: Nom de l'opération (pour les logs)

        Raises:
            FirebaseConnectionError: Après MAX_RETRIES échecs
        """
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                func()
                return
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = BACKOFF_DELAYS[attempt]
                    logger.warning(
                        f"Tentative {attempt + 1}/{MAX_RETRIES} échouée pour "
                        f"{operation_name}, nouvelle tentative dans {delay}s..."
                    )
                    time.sleep(delay)

        raise FirebaseConnectionError(
            f"Échec après {MAX_RETRIES} tentatives pour {operation_name}: "
            f"{last_error}"
        ) from last_error

    @staticmethod
    def _add_error(error_msg: str) -> None:
        """
        Ajoute une erreur aux statistiques.

        Args:
            error_msg: Message d'erreur
        """
        _sync_stats['erreurs'].append({
            'timestamp': timezone.now().isoformat(),
            'message': error_msg,
        })
        _sync_stats['dernieres_erreurs'].append(
            f"[{timezone.now().isoformat()}] {error_msg}"
        )

        # Limiter la liste des 10 dernières erreurs
        if len(_sync_stats['dernieres_erreurs']) > 10:
            _sync_stats['dernieres_erreurs'] = _sync_stats['dernieres_erreurs'][-10:]