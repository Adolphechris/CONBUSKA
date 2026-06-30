"""
approvisionnements/tests/test_frais_service.py

Tests unitaires pour FraisService.
"""

from decimal import Decimal
from django.test import TestCase

from approvisionnements.models import (
    Approvisionnement,
    DetailsApprovisionnement,
    FraisApprovisionnement,
    TypeFrais,
)
from approvisionnements.services.frais_service import FraisService
from fournisseurs.models import Fournisseur
from parametres.models import Magasin
from produits.models import Article, Categorie, Unite
from users.models import CustomUser


class FraisServiceTestCase(TestCase):
    """Tests unitaires pour FraisService."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpass123",
            force_password_change=False,
        )
        self.magasin = Magasin.objects.create(
            nom="Magasin Test",
            description="Description test",
            is_principal=True,
            localisation="Kinshasa",
        )
        self.fournisseur = Fournisseur.objects.create(
            nom="Fournisseur Test",
            telephone="+243987654321",
            email="fournisseur@test.com",
        )
        self.categorie = Categorie.objects.create(nom="Catégorie Test")
        self.unite = Unite.objects.create(nom="Pièce", description="Unité de base")
        self.article = Article.objects.create(
            designation="Article Test",
            description="Description article",
            categorie=self.categorie,
            unite=self.unite,
            prix_achat=Decimal("100.00"),
            prix_vente=Decimal("150.00"),
            prix_vente_gros=Decimal("140.00"),
            devise="FC",
            seuil=10,
            seuil_gros=20,
            emplacement="Rayon A",
        )
        self.type_transport = TypeFrais.objects.create(
            nom="Transport",
            icon="fa-truck",
            actif=True,
        )
        self.type_douane = TypeFrais.objects.create(
            nom="Douane",
            icon="fa-customs",
            actif=True,
        )
        self.appro = Approvisionnement.objects.create(
            magasin=self.magasin,
            devise="$",
            taux=Decimal("2800.00"),
            valide=False,
            cree_par=self.user,
        )
        self.detail = DetailsApprovisionnement.objects.create(
            approvisionnement=self.appro,
            fournisseur=self.fournisseur,
            facture="FACT-001",
            article=self.article,
            qte=10,
            prix=Decimal("100.00"),
        )

    def test_save_frais_creates_frais_from_cleaned_data(self):
        """save_frais crée des frais à partir des données nettoyées."""
        cleaned_data = {
            f"frais_{self.type_transport.pk}": Decimal("500.00"),
            f"frais_{self.type_douane.pk}": Decimal("300.00"),
        }
        FraisService.save_frais(self.detail, cleaned_data)

        frais_list = FraisApprovisionnement.objects.filter(detail=self.detail)
        self.assertEqual(frais_list.count(), 2)

        frais_transport = frais_list.get(type_frais=self.type_transport)
        self.assertEqual(frais_transport.montant, Decimal("500.00"))

        frais_douane = frais_list.get(type_frais=self.type_douane)
        self.assertEqual(frais_douane.montant, Decimal("300.00"))

    def test_save_frais_remplace_anciens_frais(self):
        """save_frais supprime les anciens frais avant d'en créer de nouveaux."""
        FraisApprovisionnement.objects.create(
            detail=self.detail,
            type_frais=self.type_transport,
            montant=Decimal("999.00"),
        )
        self.assertEqual(FraisApprovisionnement.objects.filter(detail=self.detail).count(), 1)

        cleaned_data = {
            f"frais_{self.type_transport.pk}": Decimal("200.00"),
        }
        FraisService.save_frais(self.detail, cleaned_data)

        frais_list = FraisApprovisionnement.objects.filter(detail=self.detail)
        self.assertEqual(frais_list.count(), 1)
        self.assertEqual(frais_list.first().montant, Decimal("200.00"))

    def test_save_frais_ignore_zero_values(self):
        """save_frais ignore les frais avec valeur 0 ou None."""
        cleaned_data = {
            f"frais_{self.type_transport.pk}": Decimal("0"),
            f"frais_{self.type_douane.pk}": None,
        }
        FraisService.save_frais(self.detail, cleaned_data)

        frais_count = FraisApprovisionnement.objects.filter(detail=self.detail).count()
        self.assertEqual(frais_count, 0)

    def test_save_frais_empty_cleaned_data(self):
        """save_frais avec un dict vide ne crée aucun frais."""
        FraisService.save_frais(self.detail, {})
        self.assertEqual(FraisApprovisionnement.objects.filter(detail=self.detail).count(), 0)

    def test_save_frais_bulk_create_ameliore_performance(self):
        """save_frais utilise bulk_create pour les performances."""
        cleaned_data = {
            f"frais_{self.type_transport.pk}": Decimal("500.00"),
            f"frais_{self.type_douane.pk}": Decimal("300.00"),
        }
        FraisService.save_frais(self.detail, cleaned_data)
        self.assertEqual(FraisApprovisionnement.objects.count(), 2)
