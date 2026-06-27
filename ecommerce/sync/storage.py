"""
Module de gestion des images Firebase Storage.

Gère l'upload, la transformation (redimensionnement, conversion WebP)
et la suppression des images d'articles vers Firebase Storage.
"""

import io
import logging
import os
from typing import Optional

from PIL import Image

from django.conf import settings

from ecommerce.exceptions import ImageTransformationError

logger = logging.getLogger('ecommerce.sync.storage')


class FirebaseStorageService:
    """
    Service de gestion des images dans Firebase Storage.

    Responsabilités :
    - Upload et transformation des images (600x600, 150x150, WebP)
    - Détection des changements d'image (via hash)
    - Suppression des images
    - Génération d'URLs publiques
    """

    # Taille des images générées
    IMAGE_SIZE = (600, 600)
    THUMB_SIZE = (150, 150)
    WEBP_QUALITY = 80

    # Dossier de base dans Storage
    STORAGE_PATH = 'articles'

    @classmethod
    def upload_article_image(cls, article, force: bool = False) -> Optional[str]:
        """
        Upload et transforme l'image d'un article vers Firebase Storage.

        Args:
            article: Instance du modèle Article
            force: Si True, force le ré-upload même si l'image n'a pas changé

        Returns:
            str: URL publique de l'image (600x600), ou None si pas d'image

        Raises:
            ImageTransformationError: Si la transformation échoue
        """
        from produits.models import Article

        # Vérifier que l'article a une image
        image_path = cls._get_image_path(article)
        if not image_path:
            logger.info(f"Article {article.code} : pas d'image locale")
            return None

        # Vérifier si l'image a changé (sauf si force=True)
        if not force and not cls._image_has_changed(article, image_path):
            logger.debug(f"Article {article.code} : image inchangée, pas d'upload")
            return cls._get_public_url(str(article.code), 'image_600.webp')

        try:
            # Charger et transformer l'image
            image = Image.open(image_path)
            
            # Convertir en RGB si nécessaire (pour WebP)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')

            # Redimensionner et uploader la version 600x600
            image_600 = cls._resize_and_crop(image, cls.IMAGE_SIZE)
            url_600 = cls._upload_image(
                article_code=str(article.code),
                image=image_600,
                filename='image_600.webp',
                content_type='image/webp',
            )

            # Redimensionner et uploader la version 150x150 (thumbnail)
            image_150 = cls._resize_and_crop(image, cls.THUMB_SIZE)
            cls._upload_image(
                article_code=str(article.code),
                image=image_150,
                filename='thumb_150.webp',
                content_type='image/webp',
            )

            # Fermer l'image originale
            image.close()

            logger.info(
                f"Article {article.code} : image uploadée avec succès → {url_600}"
            )
            return url_600

        except Exception as e:
            raise ImageTransformationError(
                f"Erreur de transformation pour l'article {article.code}: {e}"
            ) from e

    @classmethod
    def delete_article_images(cls, article_code: str) -> None:
        """
        Supprime toutes les images d'un article du Storage.

        Args:
            article_code: Code de l'article (ex: "ART001")
        """
        if not cls._is_firebase_configured():
            logger.warning(f"Firebase non configuré, suppression ignorée pour {article_code}")
            return

        try:
            bucket = cls._get_bucket()
            prefix = f"{cls.STORAGE_PATH}/{article_code}/"
            blobs = bucket.list_blobs(prefix=prefix)
            
            count = 0
            for blob in blobs:
                blob.delete()
                count += 1
            
            if count > 0:
                logger.info(f"Images supprimées pour l'article {article_code} ({count} fichier(s))")
            
        except Exception as e:
            logger.error(f"Erreur suppression images {article_code}: {e}")

    @classmethod
    def _resize_and_crop(cls, image: Image.Image, size: tuple) -> Image.Image:
        """
        Redimensionne une image en format carré (crop centré).

        Args:
            image: Image PIL à transformer
            size: Tuple (width, height) de la taille cible

        Returns:
            Image.Image: Image transformée
        """
        # Crop centré pour obtenir un carré
        width, height = image.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        
        image_cropped = image.crop((left, top, right, bottom))
        image_resized = image_cropped.resize(size, Image.LANCZOS)
        
        return image_resized

    @classmethod
    def _upload_image(
        cls,
        article_code: str,
        image: Image.Image,
        filename: str,
        content_type: str = 'image/webp',
    ) -> str:
        """
        Upload une image transformée vers Firebase Storage.

        Args:
            article_code: Code de l'article
            image: Image PIL à uploader
            filename: Nom du fichier (ex: "image_600.webp")
            content_type: Type MIME

        Returns:
            str: URL publique de l'image

        Raises:
            ImageTransformationError: Si l'upload échoue
        """
        if not cls._is_firebase_configured():
            # Mode développement : retourner l'URL simulée
            return cls._get_public_url(article_code, filename)

        try:
            bucket = cls._get_bucket()
            blob_path = f"{cls.STORAGE_PATH}/{article_code}/{filename}"
            blob = bucket.blob(blob_path)

            # Sauvegarder l'image en mémoire
            buffer = io.BytesIO()
            image.save(buffer, format='WEBP', quality=cls.WEBP_QUALITY)
            buffer.seek(0)

            # Upload vers Storage
            blob.upload_from_file(
                buffer,
                content_type=content_type,
            )

            # Rendre public
            blob.make_public()

            return blob.public_url

        except Exception as e:
            raise ImageTransformationError(
                f"Erreur upload {filename} pour {article_code}: {e}"
            ) from e

    @classmethod
    def _get_image_path(cls, article) -> Optional[str]:
        """
        Récupère le chemin absolu de l'image d'un article.

        Priorité : photo1 → photo2 → None

        Args:
            article: Instance du modèle Article

        Returns:
            str: Chemin absolu du fichier, ou None
        """
        if article.photo1 and article.photo1.name:
            path = article.photo1.path
            if os.path.exists(path):
                return path

        if article.photo2 and article.photo2.name:
            path = article.photo2.path
            if os.path.exists(path):
                return path

        return None

    @classmethod
    def _image_has_changed(cls, article, image_path: str) -> bool:
        """
        Vérifie si l'image d'un article a changé depuis la dernière sync.

        Utilise la date de modification du fichier comme indicateur.

        Args:
            article: Instance du modèle Article
            image_path: Chemin absolu du fichier image

        Returns:
            bool: True si l'image a changé (ou si c'est la première sync)
        """
        # Si c'est la première synchronisation, l'image est "changée"
        if not article.derniere_sync_firestore:
            return True

        # Vérifier la date de modification du fichier
        try:
            file_mtime = os.path.getmtime(image_path)
            from datetime import datetime
            file_dt = datetime.fromtimestamp(file_mtime)
            
            import pytz
            file_dt_aware = pytz.UTC.localize(file_dt) if hasattr(pytz, 'UTC') else file_dt
            
            if hasattr(article.derniere_sync_firestore, 'tzinfo') and article.derniere_sync_firestore.tzinfo:
                return file_dt_aware > article.derniere_sync_firestore
            
            return file_dt > article.derniere_sync_firestore.replace(tzinfo=None)
            
        except OSError:
            return True

    @staticmethod
    def _get_public_url(article_code: str, filename: str) -> str:
        """
        Génère l'URL publique d'une image dans Storage.

        En mode développement, retourne une URL simulée.
        En production, retourne l'URL réelle Firebase Storage.

        Args:
            article_code: Code de l'article
            filename: Nom du fichier

        Returns:
            str: URL publique
        """
        project_id = getattr(settings, 'FIREBASE_PROJECT_ID', 'conbuska-boutique-dev')
        bucket_name = f"{project_id}.appspot.com"
        
        return (
            f"https://firebasestorage.googleapis.com/v0/b/"
            f"{bucket_name}/o/"
            f"articles%2F{article_code}%2F{filename}?alt=media"
        )

    @staticmethod
    def _is_firebase_configured() -> bool:
        """
        Vérifie si Firebase est configuré.

        Returns:
            bool: True si les credentials Firebase sont disponibles
        """
        return bool(getattr(settings, 'FIREBASE_CREDENTIALS', None))

    @staticmethod
    def _get_bucket():
        """
        Récupère le bucket Firebase Storage.

        Returns:
            Bucket: Instance du bucket Firebase Storage

        Raises:
            ImageTransformationError: Si Firebase n'est pas configuré
        """
        try:
            from firebase_admin import storage
            bucket_name = getattr(settings, 'FIREBASE_STORAGE_BUCKET', None)
            if bucket_name:
                return storage.bucket(bucket_name)
            return storage.bucket()
        except Exception as e:
            raise ImageTransformationError(
                f"Impossible d'accéder au bucket Firebase Storage: {e}"
            ) from e