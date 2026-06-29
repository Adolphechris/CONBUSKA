"""
Test Tâche 1.1.2 – Calcul coût par lot (PAS DE MOYENNE)
Principe: Chaque lot garde son propre coût d'achat
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from parametres.models import Magasin, TauxEchange
from produits.models import Article, Categorie, Unite, Stock
from factures.models import Facture, DetailsFacture

User = get_user_model()


class CalculCoutParLotTestCase(TestCase):
    """Test du calcul du coût par lot (sans moyenne)"""

    def setUp(self):
        """Préparer les données de test"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.magasin = Magasin.objects.create(
            nom='Magasin Principal',
            is_principal=True
        )

        self.categorie = Categorie.objects.create(nom='Boulangerie')
        self.unite = Unite.objects.create(nom='Kg')

        # Article
        self.article = Article.objects.create(
            code=1000,
            designation='Farine de blé',
            description='Farine pour pain',
            categorie=self.categorie,
            unite=self.unite,
            fournisseur=None,
            prix_achat=Decimal('1000'),
            prix_vente=Decimal('1500'),
            prix_vente_gros=Decimal('2000'),
            devise='FC',
            seuil=10,
            seuil_gros=50,
            emplacement='A1-01',
            actif=True
        )

        self.taux = TauxEchange.objects.create(
            taux=2000,
            effective_date=date.today()
        )

    def test_cout_lot_simple(self):
        """Test : calcul coût d'un lot simple"""
        # Créer un lot avec coûts spécifiques
        lot = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=10,
            date_peremption=date.today() + timedelta(days=90),
            prix_achat=Decimal('1000'),      # PAN
            frais_approche=Decimal('100'),   # FA
            prix_vente_detail=Decimal('1500'),  # PVD
            prix_vente_gros=Decimal('2000')     # PVG
        )

        # Coût total du lot = PAN + FA
        cout_attendu = Decimal('1100')  # 1000 + 100
        self.assertEqual(lot.cout_total, cout_attendu)

    def test_cout_lot_sans_frais(self):
        """Test : lot sans frais supplémentaires"""
        lot = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=5,
            date_peremption=date.today() + timedelta(days=60),
            prix_achat=Decimal('800'),
            frais_approche=Decimal('0'),
            prix_vente_detail=Decimal('1200'),
            prix_vente_gros=Decimal('1800')
        )

        # Coût = PAN seulement
        cout_attendu = Decimal('800')
        self.assertEqual(lot.cout_total, cout_attendu)

    def test_cout_lot_avec_frais_eleves(self):
        """Test : lot avec frais d'approche élevés"""
        lot = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=20,
            date_peremption=date.today() + timedelta(days=120),
            prix_achat=Decimal('950'),
            frais_approche=Decimal('250'),  # Frais élevés
            prix_vente_detail=Decimal('1600'),
            prix_vente_gros=Decimal('2100')
        )

        # Coût = PAN + FA
        cout_attendu = Decimal('1200')  # 950 + 250
        self.assertEqual(lot.cout_total, cout_attendu)

    def test_marge_lot(self):
        """Test : calcul de la marge par lot"""
        lot = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=15,
            date_peremption=date.today() + timedelta(days=90),
            prix_achat=Decimal('1000'),
            frais_approche=Decimal('100'),
            prix_vente_detail=Decimal('1500'),
            prix_vente_gros=Decimal('2000')
        )

        # Vendre 5 unités
        quantite_vendue = 5
        cout_vente = lot.cout_total * quantite_vendue
        revenu_vente = lot.prix_vente_detail * quantite_vendue
        marge = revenu_vente - cout_vente

        # Vérifications
        self.assertEqual(cout_vente, Decimal('5500'))  # 1100 * 5
        self.assertEqual(revenu_vente, Decimal('7500'))  # 1500 * 5
        self.assertEqual(marge, Decimal('2000'))  # 7500 - 5500

    def test_pas_moyenne_entre_lots(self):
        """Test : PAS DE MOYENNE entre lots différents"""
        # Lot 1: acheté à 1000 FC + 100 FA
        lot1 = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=10,
            date_peremption=date.today() + timedelta(days=90),
            prix_achat=Decimal('1000'),
            frais_approche=Decimal('100'),
            prix_vente_detail=Decimal('1500'),
            prix_vente_gros=Decimal('2000')
        )

        # Lot 2: acheté à 1200 FC + 50 FA (PRIX DIFFÉRENT)
        lot2 = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=10,
            date_peremption=date.today() + timedelta(days=180),
            prix_achat=Decimal('1200'),
            frais_approche=Decimal('50'),
            prix_vente_detail=Decimal('1500'),
            prix_vente_gros=Decimal('2000')
        )

        # Chaque lot garde SON propre coût
        self.assertEqual(lot1.cout_total, Decimal('1100'))  # 1000 + 100
        self.assertEqual(lot2.cout_total, Decimal('1250'))  # 1200 + 50

        # PAS DE MOYENNE: (1100 + 1250) / 2 = 1175
        # Chaque lot est indépendant
        self.assertNotEqual(lot1.cout_total, lot2.cout_total)

    def test_cout_lot_pour_facture(self):
        """Test : utilisation du coût lot dans une facture"""
        # Créer un lot
        lot = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=20,
            date_peremption=date.today() + timedelta(days=90),
            prix_achat=Decimal('1000'),
            frais_approche=Decimal('100'),
            prix_vente_detail=Decimal('1500'),
            prix_vente_gros=Decimal('2000')
        )

        # Créer une facture
        facture = Facture.objects.create(
            devise='FC',
            taux=2000,
            remise=Decimal('0'),
            client_comptoir=None,
            cree_par=self.user,
            valide=False
        )

        # Ajouter ligne avec ce lot
        ligne = DetailsFacture.objects.create(
            facture=facture,
            article=self.article,
            qte=5,
            prix=Decimal('1500'),
            lot=lot
        )

        # Le coût de la ligne doit utiliser le coût du lot spécifique
        cout_attendu = lot.cout_total * ligne.qte
        self.assertEqual(cout_attendu, Decimal('5500'))  # 1100 * 5

    def test_plusieurs_lots_meme_article(self):
        """Test : plusieurs lots pour le même article avec coûts différents"""
        # Créer 3 lots avec coûts différents
        lot1 = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=10,
            date_peremption=date.today() + timedelta(days=60),
            prix_achat=Decimal('900'),
            frais_approche=Decimal('100'),
            prix_vente_detail=Decimal('1500'),
            prix_vente_gros=Decimal('2000')
        )

        lot2 = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=15,
            date_peremption=date.today() + timedelta(days=90),
            prix_achat=Decimal('1000'),
            frais_approche=Decimal('100'),
            prix_vente_detail=Decimal('1500'),
            prix_vente_gros=Decimal('2000')
        )

        lot3 = Stock.objects.create(
            magasin=self.magasin,
            article=self.article,
            qte=20,
            date_peremption=date.today() + timedelta(days=120),
            prix_achat=Decimal('1100'),
            frais_approche=Decimal('100'),
            prix_vente_detail=Decimal('1500'),
            prix_vente_gros=Decimal('2000')
        )

        # Chaque lot a son coût propre
        self.assertEqual(lot1.cout_total, Decimal('1000'))  # 900 + 100
        self.assertEqual(lot2.cout_total, Decimal('1100'))  # 1000 + 100
        self.assertEqual(lot3.cout_total, Decimal('1200'))  # 1100 + 100

        # Aucune moyenne calculée
        couts = [lot1.cout_total, lot2.cout_total, lot3.cout_total]
        moyenne = sum(couts) / len(couts)
        self.assertEqual(moyenne, Decimal('1100'))  # (1000+1100+1200)/3

        # Mais chaque lot garde sa valeur propre
        self.assertNotEqual(lot1.cout_total, moyenne)
        self.assertEqual(lot2.cout_total, moyenne)  # Coïncidence
        self.assertNotEqual(lot3.cout_total, moyenne)