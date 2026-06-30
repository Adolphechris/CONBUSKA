from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from produits.models import Categorie, Article
from parametres.models import TauxEchange
from django.db.models.signals import post_save, pre_delete
from produits.models import Article as ArticleModel, Stock


class ApiTests(TestCase):
    """Tests de base pour l'API REST"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disconnect Firestore signals to avoid hanging during tests
        cls._signals_disconnected = False
        try:
            from ecommerce.signals import on_article_save, on_article_delete, on_stock_save
            post_save.disconnect(on_article_save, sender=ArticleModel)
            pre_delete.disconnect(on_article_delete, sender=ArticleModel)
            post_save.disconnect(on_stock_save, sender=Stock)
            cls._signals_disconnected = True
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        if cls._signals_disconnected:
            try:
                from ecommerce.signals import on_article_save, on_article_delete, on_stock_save
                post_save.connect(on_article_save, sender=ArticleModel)
                pre_delete.connect(on_article_delete, sender=ArticleModel)
                post_save.connect(on_stock_save, sender=Stock)
            except Exception:
                pass
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        from produits.models import Unite
        self.unite = Unite.objects.create(nom="Piece", description="Pièce")
        self.categorie = Categorie.objects.create(nom="TestCat", description="Test")
        self.article = Article.objects.create(
            code=1,
            designation="Article Test",
            description="Desc",
            categorie=self.categorie,
            unite=self.unite,
            prix_vente=10.00,
            prix_vente_gros=8.00,
            devise='$',
            seuil=5,
            seuil_gros=10,
            emplacement="A1",
            est_publie=True,
        )

    def test_list_categories(self):
        """GET /api/categories/"""
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_articles(self):
        """GET /api/articles/"""
        response = self.client.get("/api/articles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_article(self):
        """GET /api/articles/{id}/"""
        response = self.client.get(f"/api/articles/{self.article.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nom"], "Article Test")

    def test_nouveautes(self):
        """GET /api/articles/nouveautes/"""
        response = self.client.get("/api/articles/nouveautes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_par_categorie(self):
        """GET /api/articles/par_categorie/?categorie=TestCat"""
        response = self.client.get("/api/articles/par_categorie/?categorie=TestCat")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_recherche(self):
        """GET /api/articles/recherche/?q=Test"""
        response = self.client.get("/api/articles/recherche/?q=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_commande_panier_vide(self):
        """POST /api/commandes/ panier vide -> 400"""
        response = self.client.post("/api/commandes/", {"articles": [], "client": {}})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_swagger_disponible(self):
        """GET /api/docs/ doit retourner 200"""
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
