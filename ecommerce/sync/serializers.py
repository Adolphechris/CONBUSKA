"""
Module de sérialisation Article → Firestore document.
Transforme les instances du modèle Article de Conbuska en documents
Firestore conformes au schéma de la collection articles_publics.
"""

import hashlib
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.utils import timezone

from ecommerce.exceptions import SyncError

logger = logging.getLogger('ecommerce.sync')


class FirestoreArticleSerializer:
    """
    Transforme une instance Article Conbuska en document Firestore.
    Gère les conversions de types (Decimal → float, DateTime → timestamp),
    les mappings de champs et les valeurs par défaut.
    """
    
    DEFAULT_IMAGE_URL = '/images/default-product.jpg'
    
    @classmethod
    def serialize(cls, article, image_url: Optional[str] = None) -> dict:
        """
        Convertit un article Conbuska en document Firestore.
        
        Args:
            article: Instance du modèle Article (produits.models.Article)
            image_url: URL publique de l'image (optionnelle)

        Returns:
            dict: Document Firestore prêt à être écrit

        Raises:
            SyncError: Si l'article est invalide
        """
        try:
            if not article.code:
                raise SyncError(f"L'article {article.designation} n'a pas de code")
            if not article.categorie:
                raise SyncError(f"L'article {article.code} n'a pas de catégorie")

            doc = {
                'nom': article.designation.strip(),
                'categorie': article.categorie.nom.strip(),
                'prix': cls._to_number(article.prix_vente),
                'devise': cls._map_devise(article.devise),
                'stock_disponible': cls._to_number(article.stock),
                'est_publie': bool(article.est_publie),
                'date_mise_a_jour': cls._to_timestamp(
                    article.derniere_sync_firestore or article.date_modification
                ),
            }

            if article.description:
                doc['description'] = article.description.strip()[:500]
            
            if article.slug:
                doc['slug'] = article.slug
            else:
                from django.utils.text import slugify
                doc['slug'] = slugify(article.designation)[:250]

            doc['image_url'] = image_url or cls._get_image_url(article)
            doc['seuil_alerte'] = cls._to_number(article.seuil)

            return doc

        except Exception as e:
            raise SyncError(
                f"Erreur de sérialisation pour l'article {article.code}: {e}"
            ) from e

    @classmethod
    def serialize_batch(cls, articles, image_urls: dict = None) -> list:
        if image_urls is None:
            image_urls = {}
        documents = []
        for article in articles:
            url = image_urls.get(str(article.code))
            try:
                doc = cls.serialize(article, image_url=url)
                documents.append(doc)
            except SyncError as e:
                logger.warning(f"Article {article.code} ignoré : {e}")
                continue
        return documents

    @classmethod
    def get_document_id(cls, article) -> str:
        return str(article.code)

    @staticmethod
    def _to_number(value) -> float:
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    @staticmethod
    def _to_timestamp(dt) -> datetime:
        if dt is None:
            return timezone.now()
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    @staticmethod
    def _map_devise(devise: str) -> str:
        mapping = {'$': 'USD', 'FC': 'CDF'}
        return mapping.get(devise, 'CDF')

    @staticmethod
    def _get_image_url(article) -> str:
        if article.photo1 and hasattr(article.photo1, 'url') and article.photo1.name:
            return article.photo1.url
        if article.photo2 and hasattr(article.photo2, 'url') and article.photo2.name:
            return article.photo2.url
        return FirestoreArticleSerializer.DEFAULT_IMAGE_URL

    @staticmethod
    def compute_image_hash(filepath: str) -> Optional[str]:
        import os
        if not os.path.exists(filepath):
            return None
        hash_md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()