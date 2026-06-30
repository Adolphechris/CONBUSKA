"""
factures/tests/test_models.py

Tests pour les modèles Facture, DetailsFacture et FactureClient.
"""

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from factures.models import Facture, DetailsFacture, FactureClient, Livreur
from factures.tests.factories import (
    ArticleFactory, ClientFactory, CustomUserFactory,
    FactureFactory,
)


class LivreurModelTestCase(TestCase):
    def test_livreur_creation(self):
        livreur = Livreur.objects.create(nom="Jean Transport", livraison=5)
        self.assertEqual(str(livreur), "Jean Transport")

    def test_livreur_default_livraison(self):
        livreur = Livreur.objects.create(nom="Paul Express")
        self.assertEqual(livreur.livraison, 0)


class FactureModelTestCase(TestCase):
    def setUp(self):
        self.user = CustomUserFactory()
        self.article = ArticleFactory()

    def test_facture_str(self):
        facture = FactureFactory(cree_par=self.user)
        self.assertEqual(str(facture), str(facture.numero))

    def test_sous_total_sans_pk(self):
        f = Facture(numero=99999, devise="FC", taux=Decimal("2800.00"))
        self.assertEqual(f.sous_total, Decimal("0"))

    def test_sous_total_avec_details(self):
        f = FactureFactory(cree_par=self.user)
        DetailsFacture.objects.create(facture=f, article=self.article, qte=3, prix=Decimal("100.00"))
        DetailsFacture.objects.create(facture=f, article=ArticleFactory(), qte=2, prix=Decimal("50.00"))
        self.assertEqual(f.sous_total, Decimal("400.00"))

    def test_total_avec_remise(self):
        f = FactureFactory(cree_par=self.user, remise=Decimal("25.00"))
        DetailsFacture.objects.create(facture=f, article=self.article, qte=5, prix=Decimal("100.00"))
        self.assertEqual(f.total, Decimal("475.00"))

    def test_total_articles_sans_pk(self):
        f = Facture(numero=88888, devise="FC", taux=Decimal("2800.00"))
        self.assertEqual(f.total_articles, 0)

    def test_get_next_numero(self):
        n = Facture.get_next_num()
        self.assertIsInstance(n, int)
        self.assertGreater(n, 0)

    def test_validation_taux_zero(self):
        f = FactureFactory(cree_par=self.user, valide=False)
        f.valide = True
        f.taux = Decimal("0")
        with self.assertRaises(ValidationError) as ctx:
            f.clean()
        self.assertIn("taux", str(ctx.exception))

    def test_validation_devise_invalide(self):
        f = FactureFactory(cree_par=self.user, valide=False)
        f.valide = True
        f.devise = "EUR"
        with self.assertRaises(ValidationError):
            f.clean()


class FactureClientModelTestCase(TestCase):
    def setUp(self):
        self.user = CustomUserFactory()
        self.facture = FactureFactory(cree_par=self.user)

    def test_facture_client_creation(self):
        client = ClientFactory()
        fc = FactureClient.objects.create(facture=self.facture, client=client)
        self.assertEqual(fc.facture, self.facture)
        self.assertEqual(fc.client, client)

    def test_facture_client_one_to_one(self):
        c1 = ClientFactory()
        c2 = ClientFactory()
        FactureClient.objects.create(facture=self.facture, client=c1)
        with self.assertRaises(Exception):
            FactureClient.objects.create(facture=self.facture, client=c2)


class DetailsFactureModelTestCase(TestCase):
    def setUp(self):
        self.user = CustomUserFactory()

    def test_details_total(self):
        d = DetailsFacture(qte=5, prix=Decimal("120.00"))
        self.assertEqual(d.total, Decimal("600.00"))

    def test_save_valeur_usd_fc(self):
        f = FactureFactory(cree_par=self.user, devise="FC", taux=Decimal("2800.00"))
        a = ArticleFactory(prix_vente=Decimal("100.00"))
        d = DetailsFacture.objects.create(facture=f, article=a, qte=5, prix=Decimal("100.00"))
        expected = Decimal("500.00") / Decimal("2800.00")
        self.assertEqual(d.valeur_usd, expected)
        self.assertEqual(d.taux_creation, Decimal("2800.00"))

    def test_save_valeur_usd_usd(self):
        f = FactureFactory(cree_par=self.user, devise="$", taux=Decimal("2800.00"))
        a = ArticleFactory(prix_vente=Decimal("50.00"))
        d = DetailsFacture.objects.create(facture=f, article=a, qte=3, prix=Decimal("50.00"))
        self.assertEqual(d.valeur_usd, Decimal("150.00"))

    def test_save_preserve_historical(self):
        f = FactureFactory(cree_par=self.user, devise="FC", taux=Decimal("2800.00"))
        a = ArticleFactory(prix_vente=Decimal("100.00"))
        d = DetailsFacture.objects.create(facture=f, article=a, qte=5, prix=Decimal("100.00"))
        original_taux = d.taux_creation
        d.qte = 10
        d.save()
        d.refresh_from_db()
        self.assertEqual(d.taux_creation, original_taux)
        self.assertEqual(d.valeur_usd, Decimal("0.1786"))

    def test_delete_cascade(self):
        f = FactureFactory(cree_par=self.user)
        a = ArticleFactory()
        d = DetailsFacture.objects.create(facture=f, article=a, qte=2, prix=Decimal("100.00"))
        pk = d.pk
        # PROTECT cascade: must delete details first, then facture
        DetailsFacture.objects.filter(facture=f).delete()
        f.delete()
        self.assertFalse(DetailsFacture.objects.filter(pk=pk).exists())


class FactureVentesJournalieresTestCase(TestCase):
    def setUp(self):
        self.user = CustomUserFactory()

    def test_ventes_journalieres(self):
        today = timezone.now().date()
        f = FactureFactory(cree_par=self.user, date_facture=today, valide=True)
        a = ArticleFactory()
        DetailsFacture.objects.create(facture=f, article=a, qte=2, prix=Decimal("100.00"))
        results = list(Facture.objects.ventes_journalieres())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["total_vendu"], Decimal("200.00"))
