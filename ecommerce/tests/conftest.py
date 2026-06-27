"""
Fixtures pour les tests du module e-commerce.
Réutilise les factories existantes du module produits.
Tous les appels Firestore sont mockés pour éviter
les dépendances externes pendant les tests.
"""

from unittest.mock import patch
import pytest
from decimal import Decimal


@pytest.fixture(autouse=True)
def mock_firebase():
    """
    Mock tous les appels Firestore/Storage pendant les tests.
    Appliqué automatiquement à tous les tests du module e-commerce.
    """
    with patch('ecommerce.sync.services.FirestoreSyncService.sync_article'):
        with patch('ecommerce.sync.services.FirestoreSyncService.delete_article'):
            with patch('ecommerce.sync.services.FirestoreSyncService._get_firestore_client'):
                with patch('ecommerce.sync.services.FirestoreSyncService._execute_with_retry'):
                    with patch('ecommerce.sync.storage.FirebaseStorageService.upload_article_image',
                               return_value='https://storage.example.com/test.webp'):
                        with patch('ecommerce.sync.storage.FirebaseStorageService.delete_article_images'):
                            yield


@pytest.fixture
def article_publie(db):
    """Crée un article publié pour les tests."""
    from produits.tests.factories import ArticleFactory
    from parametres.models import Magasin
    
    Magasin.objects.get_or_create(
        nom="Magasin Principal",
        defaults={
            "description": "Magasin principal pour les tests",
            "localisation": "Kinshasa",
            "is_principal": True,
        },
    )
    
    article = ArticleFactory(
        code=3001,
        designation="Article Test Publié",
        description="Description de test",
        prix_vente=Decimal('1500.00'),
        devise='FC',
        est_publie=True,
        seuil=5,
    )
    return article


@pytest.fixture
def article_non_publie(db):
    """Crée un article non publié pour les tests."""
    from produits.tests.factories import ArticleFactory
    
    article = ArticleFactory(
        code=3002,
        designation="Article Test Non Publié",
        est_publie=False,
    )
    return article


@pytest.fixture
def article_sans_code(db):
    """Crée un article sans code pour les tests d'erreur."""
    from produits.tests.factories import ArticleFactory
    from parametres.models import Magasin
    
    Magasin.objects.get_or_create(
        nom="Magasin Principal",
        defaults={
            "description": "Test",
            "localisation": "Kinshasa",
            "is_principal": True,
        },
    )
    
    article = ArticleFactory(
        code=3003,
        designation="Article Sans Code",
        est_publie=True,
    )
    article.code = None
    return article