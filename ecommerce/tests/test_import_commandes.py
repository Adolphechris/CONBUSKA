"""
Tests unitaires et d'intégration pour le module d'import des commandes.

Tests couverts:
- Vérification articles existants
- Vérification stocks suffisants
- Création/trouver client
- Création facture
- Gestion erreurs
- Statistiques
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model

from ecommerce.sync.import_commandes import ImportCommandesService
from produits.models import Article, Magasin, Stock, Categorie, Unite
from clients.models import Client
from factures.models import Facture, FactureClient


class TestVerificationArticles(TestCase):
    """Tests pour la vérification des articles."""
    
    def setUp(self):
        """Créer des articles de test."""
        self.article_existant = Article.objects.create(
            code=1001,
            designation="Article Test",
            prix_vente=1000,
            devise="FC",
            seuil=5,
            seuil_gros=10,
            categorie=Categorie.objects.create(nom="Test", description=""),
            unite=Unite.objects.create(nom="Unite Test", description="")
        )
    
    def test_article_existant_ok(self):
        """Article existant → validation OK."""
        lignes = [{'code_article': '1001', 'quantite': 1}]
        resultat = ImportCommandesService._verifier_articles(lignes)
        
        self.assertTrue(resultat['valide'])
        self.assertEqual(resultat['erreur'], '')
    
    def test_article_inexistant_erreur(self):
        """Article inexistant → erreur."""
        lignes = [{'code_article': '9999', 'quantite': 1}]
        resultat = ImportCommandesService._verifier_articles(lignes)
        
        self.assertFalse(resultat['valide'])
        self.assertIn('Article inconnu', resultat['erreur'])
        self.assertIn('9999', resultat['erreur'])
    
    def test_code_article_invalide(self):
        """Code article invalide (non convertible en int) → erreur."""
        lignes = [{'code_article': 'ABC', 'quantite': 1}]
        resultat = ImportCommandesService._verifier_articles(lignes)
        
        self.assertFalse(resultat['valide'])
        self.assertIn('code invalide', resultat['erreur'])
    
    def test_code_article_manquant(self):
        """Code article manquant → erreur."""
        lignes = [{'quantite': 1}]  # Pas de code_article
        resultat = ImportCommandesService._verifier_articles(lignes)
        
        self.assertFalse(resultat['valide'])
        self.assertIn('manquant', resultat['erreur'])
    
    def test_multiple_articles_un_inexistant(self):
        """Si un article sur plusieurs est inexistant → erreur."""
        lignes = [
            {'code_article': '1001', 'quantite': 1},
            {'code_article': '9999', 'quantite': 2}
        ]
        resultat = ImportCommandesService._verifier_articles(lignes)
        
        self.assertFalse(resultat['valide'])
        self.assertIn('9999', resultat['erreur'])


class TestVerificationStocks(TestCase):
    """Tests pour la vérification des stocks."""
    
    def setUp(self):
        """Créer un magasin et un article avec stock."""
        self.magasin = Magasin.objects.create(
            nom="Magasin Principal",
            is_principal=True
        )
        
        self.article = Article.objects.create(
            code=1001,
            designation="Article Test",
            prix_vente=1000,
            devise="FC",
            seuil=5,
            seuil_gros=10,
            categorie=Categorie.objects.create(nom="Test", description=""),
            unite=Unite.objects.create(nom="Unite Test", description="")
        )
        
        # Créer un lot de stock
        self.stock = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=100,
            date_peremption="2026-12-31"
        )
    
    def test_stock_suffisant_ok(self):
        """Stock suffisant → validation OK."""
        lignes = [{'code_article': '1001', 'quantite': 50, 'nom_article': 'Test'}]
        resultat = ImportCommandesService._verifier_stocks(lignes)
        
        self.assertTrue(resultat['valide'])
        self.assertEqual(resultat['erreur'], '')
    
    def test_stock_insuffisant_erreur(self):
        """Stock insuffisant → erreur."""
        lignes = [{'code_article': '1001', 'quantite': 150, 'nom_article': 'Test'}]
        resultat = ImportCommandesService._verifier_stocks(lignes)
        
        self.assertFalse(resultat['valide'])
        self.assertIn('Stock insuffisant', resultat['erreur'])
        self.assertIn('Test', resultat['erreur'])
        self.assertIn('150', resultat['erreur'])
        self.assertIn('100', resultat['erreur'])
    
    def test_stock_exact_ok(self):
        """Stock exact (quantité demandée = stock disponible) → OK."""
        lignes = [{'code_article': '1001', 'quantite': 100, 'nom_article': 'Test'}]
        resultat = ImportCommandesService._verifier_stocks(lignes)
        
        self.assertTrue(resultat['valide'])
    
    def test_article_inexistant_stock(self):
        """Article inexistant → erreur."""
        lignes = [{'code_article': '9999', 'quantite': 1, 'nom_article': 'Test'}]
        resultat = ImportCommandesService._verifier_stocks(lignes)
        
        self.assertFalse(resultat['valide'])
        self.assertIn('Article inconnu', resultat['erreur'])
    
    def test_aucun_magasin_principal(self):
        """Pas de magasin principal → erreur."""
        Magasin.objects.filter(is_principal=True).delete()
        
        lignes = [{'code_article': '1001', 'quantite': 1, 'nom_article': 'Test'}]
        resultat = ImportCommandesService._verifier_stocks(lignes)
        
        self.assertFalse(resultat['valide'])
        self.assertIn('magasin principal', resultat['erreur'].lower())


class TestCreationClient(TestCase):
    """Tests pour la création/trouver client."""
    
    def test_trouver_client_existant(self):
        """Client existant → retourné."""
        client = Client.objects.create(
            code=3001,
            nom="Jean Dupont",
            email="jean@example.com",
            telephone="0123456789",
            adresse="123 Rue Test"
        )
        
        client_data = {
            'nom': 'Jean Dupont',
            'email': 'jean@example.com',
            'telephone': '0123456789',
            'adresse': '123 Rue Test'
        }
        
        resultat = ImportCommandesService._creer_ou_trouver_client(client_data)
        
        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.code, 3001)
        self.assertEqual(resultat.email, 'jean@example.com')
    
    def test_creer_nouveau_client(self):
        """Nouveau client → créé."""
        client_data = {
            'nom': 'Nouveau Client',
            'email': 'nouveau@example.com',
            'telephone': '0987654321',
            'adresse': '456 Avenue Test'
        }
        
        resultat = ImportCommandesService._creer_ou_trouver_client(client_data)
        
        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.nom, 'Nouveau Client')
        self.assertEqual(resultat.email, 'nouveau@example.com')
        self.assertTrue(resultat.code > 3000)  # Code auto-généré
    
    def test_email_manquant(self):
        """Email manquant → None."""
        client_data = {
            'nom': 'Client Test',
            'email': '',  # Vide
        }
        
        resultat = ImportCommandesService._creer_ou_trouver_client(client_data)
        
        self.assertIsNone(resultat)
    
    def test_email_normalise(self):
        """Email doit être normalisé (lowercase)."""
        client_data = {
            'nom': 'Client Test',
            'email': 'TEST@EXAMPLE.COM',  # Majuscules
        }
        
        resultat = ImportCommandesService._creer_ou_trouver_client(client_data)
        
        self.assertIsNotNone(resultat)
        self.assertEqual(resultat.email, 'test@example.com')


class TestImportStats(TestCase):
    """Tests pour les statistiques d'import."""
    
    def test_get_import_stats_vide(self):
        """Stats vides au début."""
        stats = ImportCommandesService.get_import_stats()
        
        self.assertIsNone(stats['dernier_import'])
        self.assertEqual(stats['commandes_importees'], 0)
        self.assertEqual(stats['commandes_en_erreur'], 0)
        self.assertEqual(len(stats['dernieres_erreurs']), 0)
    
    def test_get_import_stats_avec_erreurs(self):
        """Stats avec erreurs."""
        # Simuler des erreurs
        ImportCommandesService._add_error("Erreur test 1")
        ImportCommandesService._add_error("Erreur test 2")
        
        stats = ImportCommandesService.get_import_stats()
        
        self.assertEqual(len(stats['dernieres_erreurs']), 2)
        self.assertIn('Erreur test 1', stats['dernieres_erreurs'][0])
    
    def test_limite_erreurs_5(self):
        """Maximum 5 erreurs gardées."""
        for i in range(10):
            ImportCommandesService._add_error(f"Erreur {i}")
        
        stats = ImportCommandesService.get_import_stats()
        
        self.assertEqual(len(stats['dernieres_erreurs']), 5)
        # Les 5 dernières doivent être présentes
        self.assertIn('Erreur 5', stats['dernieres_erreurs'][0])
        self.assertIn('Erreur 9', stats['dernieres_erreurs'][4])


# Tests d'intégration (nécessitent Firebase configuré)
class TestImportIntegration(TransactionTestCase):
    """Tests d'intégration (avec base de test)."""
    
    def setUp(self):
        """Préparer l'environnement de test."""
        self.magasin = Magasin.objects.create(
            nom="Magasin Test",
            is_principal=True
        )
        
        self.article = Article.objects.create(
            code=1001,
            designation="Article Test",
            prix_vente=1000,
            devise="FC",
            seuil=5,
            seuil_gros=10,
            categorie=Categorie.objects.create(nom="Test", description=""),
            unite=Unite.objects.create(nom="Unite Test", description="")
        )
        
        Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=100,
            date_peremption="2026-12-31"
        )
    
    @patch('ecommerce.sync.import_commandes.FirestoreSyncService')
    def test_import_commande_valide(self, mock_firestore):
        """Test import d'une commande valide."""
        # Mock Firestore
        mock_db = MagicMock()
        mock_firestore._get_firestore_client.return_value = mock_db
        
        # Simuler une commande Firestore
        mock_doc = MagicMock()
        mock_doc.id = 'CMD001'
        mock_doc.to_dict.return_value = {
            'date_commande': '2026-06-27T20:00:00Z',
            'client': {
                'nom': 'Client Test',
                'email': 'client@test.com',
                'telephone': '0123456789',
                'adresse': '123 Rue Test'
            },
            'lignes': [
                {
                    'code_article': '1001',
                    'quantite': 2,
                    'prix_unitaire': 1000,
                    'nom_article': 'Article Test'
                }
            ],
            'total': 2000
        }
        
        mock_db.collection.return_value.where.return_value.stream.return_value = [mock_doc]
        
        # Exécuter l'import
        resultat = ImportCommandesService.importer_commandes(limit=1)
        
        # Vérifications
        self.assertEqual(resultat['succes'], 1)
        self.assertEqual(resultat['erreurs'], 0)
        
        # Vérifier que la facture a été créée
        factures = Facture.objects.filter(valide=True)
        self.assertEqual(factures.count(), 1)
        
        # Vérifier que le stock a été décrémenté
        stock = Stock.objects.get(article=self.article)
        self.assertEqual(stock.qte, 98)  # 100 - 2
    
    @patch('ecommerce.sync.import_commandes.FirestoreSyncService')
    def test_import_article_inexistant(self, mock_firestore):
        """Test import avec article inexistant."""
        mock_db = MagicMock()
        mock_firestore._get_firestore_client.return_value = mock_db
        
        mock_doc = MagicMock()
        mock_doc.id = 'CMD001'
        mock_doc.to_dict.return_value = {
            'date_commande': '2026-06-27T20:00:00Z',
            'client': {
                'nom': 'Client Test',
                'email': 'client@test.com',
                'telephone': '0123456789',
                'adresse': '123 Rue Test'
            },
            'lignes': [
                {
                    'code_article': '9999',  # Article inexistant
                    'quantite': 1,
                    'prix_unitaire': 1000,
                    'nom_article': 'Article Inexistant'
                }
            ],
            'total': 1000
        }
        
        mock_db.collection.return_value.where.return_value.stream.return_value = [mock_doc]
        
        resultat = ImportCommandesService.importer_commandes(limit=1)
        
        # Vérifications
        self.assertEqual(resultat['succes'], 0)
        self.assertEqual(resultat['erreurs'], 1)
        self.assertIn('Article inconnu', resultat['details'][0]['erreur'])
        
        # Vérifier qu'aucune facture n'a été créée
        factures = Facture.objects.filter(valide=True)
        self.assertEqual(factures.count(), 0)
    
    @patch('ecommerce.sync.import_commandes.FirestoreSyncService')
    def test_import_stock_insuffisant(self, mock_firestore):
        """Test import avec stock insuffisant."""
        mock_db = MagicMock()
        mock_firestore._get_firestore_client.return_value = mock_db
        
        mock_doc = MagicMock()
        mock_doc.id = 'CMD001'
        mock_doc.to_dict.return_value = {
            'date_commande': '2026-06-27T20:00:00Z',
            'client': {
                'nom': 'Client Test',
                'email': 'client@test.com',
                'telephone': '0123456789',
                'adresse': '123 Rue Test'
            },
            'lignes': [
                {
                    'code_article': '1001',
                    'quantite': 200,  # Plus que le stock disponible (100)
                    'prix_unitaire': 1000,
                    'nom_article': 'Article Test'
                }
            ],
            'total': 200000
        }
        
        mock_db.collection.return_value.where.return_value.stream.return_value = [mock_doc]
        
        resultat = ImportCommandesService.importer_commandes(limit=1)
        
        # Vérifications
        self.assertEqual(resultat['succes'], 0)
        self.assertEqual(resultat['erreurs'], 1)
        self.assertIn('Stock insuffisant', resultat['details'][0]['erreur'])
        
        # Vérifier que le stock n'a pas été modifié
        stock = Stock.objects.get(article=self.article)
        self.assertEqual(stock.qte, 100)  # Inchangé