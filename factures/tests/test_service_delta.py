"""
factures/tests/test_service_delta.py

Tests pour les opérations delta du FactureService.
Couverture : phases DRAFT et CONFIRMED, approche delta O(1).
"""

from decimal import Decimal
from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from factures.models import DetailsFacture
from factures.services import FactureService
from factures.tests.factories import (
    ArticleFactory,
    CustomUserFactory,
    DetailsFactureFactory,
    FactureFactory,
)
from parametres.models import Magasin
from produits.models import Stock, MouvementStock


class FactureServiceDeltaDraftTestCase(TestCase):
    """Tests des opérations en phase DRAFT (aucun mouvement stock)."""

    def setUp(self):
        self.user = CustomUserFactory()
        self.magasin = Magasin.objects.create(
            nom="Magasin Test", is_principal=True,
            localisation="Kinshasa", description="Test",
        )
        self.article = ArticleFactory(
            prix_vente=Decimal("100.00"), seuil_gros=10,
            prix_vente_gros=Decimal("80.00"),
        )
        # Créer du stock pour l'article
        Stock.objects.create(
            magasin=self.magasin, article=self.article, qte=100,
            date_peremption=date(2030, 12, 31),
        )
        self.facture = FactureFactory(cree_par=self.user, client_comptoir="Client Comptoir")
        DetailsFactureFactory(facture=self.facture, article=self.article, qte=2)

    def test_ajouter_article_quantite_negative_raise(self):
        """ajouter_article_facture avec qte <= 0 lève ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            FactureService.ajouter_article_facture(
                self.facture, self.article, qte=-1,
            )
        self.assertIn("strictement positive", str(ctx.exception))

    def test_modifier_article_draft_sans_mouvement_stock(self):
        """modifier_article_facture en DRAFT ne crée AUCUN mouvement stock."""
        MouvementStock.objects.all().delete()
        FactureService.modifier_article_facture(
            self.facture, self.article, qte_nouvelle=10,
        )
        self.assertEqual(MouvementStock.objects.count(), 0)

    def test_modifier_article_draft_met_a_jour_prix_gros(self):
        """modifier_article en DRAFT applique le prix de gros si seuil atteint."""
        article_bulk = ArticleFactory(
            seuil_gros=10, prix_vente=Decimal("100.00"),
            prix_vente_gros=Decimal("80.00"),
        )
        Stock.objects.create(
            magasin=self.magasin, article=article_bulk, qte=100,
            date_peremption=date(2030, 12, 31),
        )
        detail = FactureService.modifier_article_facture(
            self.facture, article_bulk, qte_nouvelle=15,
        )
        self.assertEqual(detail.qte, 15)
        self.assertEqual(detail.prix, Decimal("80.00"))

    def test_modifier_article_draft_garde_prix_normal(self):
        """modifier_article en DRAFT garde le prix normal si seuil non atteint."""
        detail = FactureService.modifier_article_facture(
            self.facture, self.article, qte_nouvelle=3,
        )
        self.assertEqual(detail.qte, 3)
        self.assertEqual(detail.prix, self.article.prix_vente)

    def test_modifier_article_qte_zero(self):
        """modifier avec qte = 0 met qte à 0 sans mouvement."""
        detail = FactureService.modifier_article_facture(
            self.facture, self.article, qte_nouvelle=0,
        )
        self.assertEqual(detail.qte, 0)

    def test_modifier_article_qte_negative_raise(self):
        """modifier avec qte négative lève ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            FactureService.modifier_article_facture(
                self.facture, self.article, qte_nouvelle=-1,
            )
        self.assertIn("négative", str(ctx.exception))


class FactureServiceDeltaConfirmedTestCase(TestCase):
    """Tests des opérations delta en phase CONFIRMED (facture validée)."""

    def setUp(self):
        self.user = CustomUserFactory()
        self.magasin = Magasin.objects.create(
            nom="Magasin Test", is_principal=True,
            localisation="Kinshasa", description="Test",
        )
        self.article = ArticleFactory(prix_achat=Decimal("50.00"),
                                       prix_vente=Decimal("100.00"))
        self.stock = Stock.objects.create(
            magasin=self.magasin, article=self.article, qte=100,
            date_peremption=date(2030, 12, 31),
        )
        self.facture = FactureFactory(
            cree_par=self.user, client_comptoir="Client Test",
            devise="$", taux=Decimal("1.00"),
        )
        DetailsFactureFactory(facture=self.facture, article=self.article, qte=10)
        FactureService.valider(facture=self.facture, user=self.user)
        self.facture.refresh_from_db()
        self.assertTrue(self.facture.valide)
        # Rafraîchir le stock après validation (consommé par valider)
        self.stock.refresh_from_db()

    def test_ajouter_article_confirmed_consomme_stock(self):
        """ajouter_article_facture en CONFIRMED crée un OUT supplémentaire."""
        qte_avant = self.stock.qte
        FactureService.ajouter_article_facture(self.facture, self.article, qte=5)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.qte, qte_avant - 5)

    def test_modifier_article_confirmed_delta_positif(self):
        """modifier_article en CONFIRMED crée 1 OUT si delta > 0."""
        qte_avant = self.stock.qte
        FactureService.modifier_article_facture(
            self.facture, self.article, qte_nouvelle=15,
        )
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.qte, qte_avant - 5)

    def test_modifier_article_confirmed_delta_negatif(self):
        """modifier_article en CONFIRMED restitue si delta < 0."""
        qte_avant = self.stock.qte
        FactureService.modifier_article_facture(
            self.facture, self.article, qte_nouvelle=7,
        )
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.qte, qte_avant + 3)

    def test_supprimer_article_confirmed_restaure_stock(self):
        """supprimer_article_facture en CONFIRMED restitue le stock."""
        qte_avant = self.stock.qte
        FactureService.supprimer_article_facture(self.facture, self.article)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.qte, qte_avant + 10)
        self.assertFalse(
            DetailsFacture.objects.filter(facture=self.facture, article=self.article).exists()
        )

    def test_supprimer_facture_confirmed_restaure_stock(self):
        """FactureService.supprimer en CONFIRMED annule tous les mouvements."""
        qte_avant = self.stock.qte
        FactureService.supprimer(facture=self.facture)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.qte, qte_avant + 10)

    def test_double_validation_raise(self):
        """Double validation lève ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            FactureService.valider(facture=self.facture, user=self.user)
        self.assertIn("déjà validée", str(ctx.exception))

    def test_get_qte_confirmee_apres_modifications(self):
        """_get_qte_confirmee retourne la quantité nette après modifications."""
        FactureService.ajouter_article_facture(self.facture, self.article, qte=3)
        FactureService.modifier_article_facture(
            self.facture, self.article, qte_nouvelle=8,
        )
        qte = FactureService._get_qte_confirmee(self.facture, self.article)
        self.assertEqual(qte, 8)
