"""
Tests pour le module de sérialisation Firestore.
"""

from decimal import Decimal
import pytest

from ecommerce.exceptions import SyncError
from ecommerce.sync.serializers import FirestoreArticleSerializer


class TestFirestoreArticleSerializer:
    """Tests pour FirestoreArticleSerializer."""

    def test_serialize_article_basique(self, article_publie):
        """Test la sérialisation d'un article standard."""
        doc = FirestoreArticleSerializer.serialize(article_publie)
        
        assert doc['nom'] == "Article Test Publié"
        assert doc['prix'] == 1500.0
        assert doc['devise'] == 'CDF'
        assert doc['est_publie'] is True
        assert 'slug' in doc
        assert doc['seuil_alerte'] == 5.0

    def test_serialize_devise_usd(self, article_publie):
        """Test la conversion de devise $ → USD."""
        article_publie.devise = '$'
        doc = FirestoreArticleSerializer.serialize(article_publie)
        assert doc['devise'] == 'USD'

    def test_serialize_devise_fc(self, article_publie):
        """Test la conversion de devise FC → CDF."""
        doc = FirestoreArticleSerializer.serialize(article_publie)
        assert doc['devise'] == 'CDF'

    def test_serialize_non_publie(self, article_non_publie):
        """Test qu'un article non publié a est_publie=False."""
        doc = FirestoreArticleSerializer.serialize(article_non_publie)
        assert doc['est_publie'] is False

    def test_serialize_sans_code_leve_erreur(self, article_sans_code):
        """Test qu'un article sans code lève SyncError."""
        with pytest.raises(SyncError):
            FirestoreArticleSerializer.serialize(article_sans_code)

    def test_get_document_id(self, article_publie):
        """Test que l'ID du document est le code article."""
        doc_id = FirestoreArticleSerializer.get_document_id(article_publie)
        assert doc_id == "3001"

    def test_compute_image_hash(self, tmp_path):
        """Test le calcul du hash MD5 d'une image."""
        image_file = tmp_path / "test_image.jpg"
        image_file.write_bytes(b"fake_image_content")
        
        hash_result = FirestoreArticleSerializer.compute_image_hash(str(image_file))
        assert hash_result is not None
        assert len(hash_result) == 32  # MD5 hex digest

    def test_compute_image_hash_fichier_inexistant(self):
        """Test que le hash retourne None si le fichier n'existe pas."""
        hash_result = FirestoreArticleSerializer.compute_image_hash("/inexistant.jpg")
        assert hash_result is None