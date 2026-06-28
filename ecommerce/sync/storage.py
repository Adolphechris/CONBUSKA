"""
Service de stockage Firebase pour les images des articles.

Gère :
- Upload d'images vers Firebase Storage
- Transformation (redimensionnement, conversion WebP, compression)
- Génération d'URLs publiques
- Suppression d'images
- Cache et optimisation
"""

import logging
import hashlib
from io import BytesIO
from typing import Dict, Optional, Tuple
from django.core.files.base import ContentFile
from django.conf import settings

from ecommerce.exceptions import ImageTransformationError

logger = logging.getLogger('ecommerce.storage')

# Constantes
IMAGE_SIZES = {
    'principal': (600, 600),
    'thumbnail': (150, 150),
}
WEBP_QUALITY = 80
MAX_RETRIES = 3


class FirebaseStorageService:
    """
    Service de gestion des images Firebase Storage.
    
    Responsabilités :
    - Upload d'images avec transformations
    - Génération d'URLs publiques
    - Suppression d'images
    - Gestion des erreurs (retry)
    """
    
    @staticmethod
    def upload_article_image(article, force: bool = False) -> Optional[str]:
        """
        Upload l'image d'un article vers Firebase Storage.
        
        Args:
            article: Instance du modèle Article
            force: Si True, force l'upload même si l'image n'a pas changé
        
        Returns:
            URL publique de l'image principale (600x600) ou None si erreur
        
        Raises:
            ImageTransformationError: Si la transformation d'image échoue
        """
        try:
            # Vérifier si l'article a une image
            if not hasattr(article, 'image_principale') or not article.image_principale:
                logger.debug(f"Article {article.code}: pas d'image, utilisation de l'image par défaut")
                return getattr(settings, 'IMAGE_DEFAUT_URL', None)
            
            image_field = article.image_principale.image_originale
            
            if not image_field:
                return getattr(settings, 'IMAGE_DEFAUT_URL', None)
            
            # Vérifier si l'image a changé (hash MD5)
            if not force and hasattr(article, 'image_hash'):
                image_hash = FirebaseStorageService._calculate_file_hash(image_field)
                if image_hash == article.image_hash:
                    logger.debug(f"Article {article.code}: image inchangée, upload ignoré")
                    return article.image_url if hasattr(article, 'image_url') else None
            
            # Ouvrir l'image avec Pillow
            from PIL import Image
            
            image_file = image_field.open('rb')
            img = Image.open(image_file)
            
            # Convertir en RGB si nécessaire (pour WebP)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Générer le nom de fichier
            code_article = str(article.code)
            filename_base = f"articles/{code_article}/image"
            
            # Traiter et uploader les deux tailles
            urls = {}
            
            # Image principale 600x600
            img_600 = FirebaseStorageService._resize_and_crop(img, (600, 600))
            url_600 = FirebaseStorageService._upload_to_storage(
                img_600, 
                f"{filename_base}_600.webp"
            )
            urls['principale'] = url_600
            
            # Thumbnail 150x150
            img_150 = FirebaseStorageService._resize_and_crop(img, (150, 150))
            url_150 = FirebaseStorageService._upload_to_storage(
                img_150, 
                f"{filename_base}_150.webp"
            )
            urls['thumbnail'] = url_150
            
            # Fermer le fichier
            image_file.close()
            
            # Mettre à jour le hash de l'image
            if not hasattr(article, 'image_hash'):
                article.image_hash = FirebaseStorageService._calculate_file_hash(image_field)
            
            logger.info(f"Article {article.code}: images uploadées avec succès")
            
            return url_600
            
        except Exception as e:
            error_msg = f"Erreur upload image article {article.code}: {e}"
            logger.error(error_msg, exc_info=True)
            raise ImageTransformationError(error_msg) from e
    
    @staticmethod
    def delete_article_images(code_article: str) -> bool:
        """
        Supprime toutes les images d'un article de Firebase Storage.
        
        Args:
            code_article: Code de l'article
        
        Returns:
            True si la suppression a réussi
        """
        try:
            from firebase_admin import storage
            
            bucket = storage.bucket()
            
            # Supprimer tous les fichiers du dossier articles/{code}/
            blobs = bucket.list_blobs(prefix=f"articles/{code_article}/")
            
            for blob in blobs:
                blob.delete()
                logger.debug(f"Supprimé: {blob.name}")
            
            logger.info(f"Article {code_article}: images supprimées de Storage")
            return True
            
        except Exception as e:
            error_msg = f"Erreur suppression images article {code_article}: {e}"
            logger.error(error_msg, exc_info=True)
            return False
    
    @staticmethod
    def _resize_and_crop(img, target_size: Tuple[int, int]):
        """
        Redimensionne et crop une image au format carré.
        
        Args:
            img: Image PIL
            target_size: Taille cible (width, height)
        
        Returns:
            Image redimensionnée et croppée
        """
        from PIL import Image
        
        # Calculer les dimensions pour crop carré
        width, height = img.size
        min_side = min(width, height)
        
        # Calculer les coordonnées de crop (centré)
        left = (width - min_side) / 2
        top = (height - min_side) / 2
        right = (width + min_side) / 2
        bottom = (height + min_side) / 2
        
        # Crop carré
        img_cropped = img.crop((left, top, right, bottom))
        
        # Redimensionner
        img_resized = img_cropped.resize(target_size, Image.Resampling.LANCZOS)
        
        return img_resized
    
    @staticmethod
    def _upload_to_storage(img, filename: str) -> str:
        """
        Upload une image vers Firebase Storage en format WebP.
        
        Args:
            img: Image PIL
            filename: Nom du fichier dans Storage
        
        Returns:
            URL publique de l'image
        """
        from firebase_admin import storage
        
        # Convertir en WebP
        buffer = BytesIO()
        img.save(buffer, format='WEBP', quality=WEBP_QUALITY, optimize=True)
        buffer.seek(0)
        
        # Upload vers Storage
        bucket = storage.bucket()
        blob = bucket.blob(filename)
        
        # Définir le content type
        blob.upload_from_file(
            buffer,
            content_type='image/webp'
        )
        
        # Rendre public
        blob.make_public()
        
        # Retourner l'URL publique
        return blob.public_url
    
    @staticmethod
    def _calculate_file_hash(image_field) -> str:
        """
        Calcule le hash MD5 d'un fichier image.
        
        Args:
            image_field: Champ ImageField Django
        
        Returns:
            Hash MD5 hexadécimal
        """
        md5 = hashlib.md5()
        
        # Lire le fichier par chunks pour ne pas charger en mémoire
        for chunk in image_field.chunks():
            md5.update(chunk)
        
        return md5.hexdigest()
    
    @staticmethod
    def get_public_url(code_article: str, size: str = 'principale') -> Optional[str]:
        """
        Génère l'URL publique d'une image d'article.
        
        Args:
            code_article: Code de l'article
            size: Taille souhaitée ('principale' ou 'thumbnail')
        
        Returns:
            URL publique ou None
        """
        try:
            from firebase_admin import storage
            
            bucket = storage.bucket()
            filename = f"articles/{code_article}/image_{size}.webp"
            
            blob = bucket.blob(filename)
            blob.reload()  # Vérifier que le fichier existe
            
            return blob.public_url
            
        except Exception as e:
            logger.warning(f"Image non trouvée pour article {code_article}: {e}")
            return None
    
    @staticmethod
    def image_exists(code_article: str, size: str = 'principale') -> bool:
        """
        Vérifie si une image existe dans Storage.
        
        Args:
            code_article: Code de l'article
            size: Taille à vérifier ('principale' ou 'thumbnail')
        
        Returns:
            True si l'image existe
        """
        try:
            from firebase_admin import storage
            
            bucket = storage.bucket()
            filename = f"articles/{code_article}/image_{size}.webp"
            
            blob = bucket.blob(filename)
            blob.reload()
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def get_storage_usage() -> Dict:
        """
        Retourne des statistiques sur l'utilisation du Storage.
        
        Returns:
            Dict avec statistiques (nombre d'images, taille totale)
        """
        try:
            from firebase_admin import storage
            
            bucket = storage.bucket()
            
            total_size = 0
            total_files = 0
            
            blobs = bucket.list_blobs(prefix="articles/")
            for blob in blobs:
                total_files += 1
                total_size += blob.size
            
            return {
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul usage Storage: {e}")
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'total_size_gb': 0,
            }