"""
factures/tests/factories.py

Factories factory-boy pour les tests du module factures.
"""

import factory
from decimal import Decimal
from factory.django import DjangoModelFactory

from users.models import CustomUser
from produits.models import Article, Categorie, Unite
from fournisseurs.models import Fournisseur
from clients.models import Client
from factures.models import Facture, DetailsFacture, Livreur, FactureClient


class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True
    type_profile = None


class LivreurFactory(DjangoModelFactory):
    class Meta:
        model = Livreur

    nom = factory.Sequence(lambda n: f"Livreur {n}")
    livraison = 0


class FactureFactory(DjangoModelFactory):
    class Meta:
        model = Facture

    numero = factory.Sequence(lambda n: 260001 + n)
    devise = "FC"
    taux = Decimal("2800.00")
    client_comptoir = None
    livreur = None
    cree_par = factory.SubFactory(CustomUserFactory)
    valide = False
    actif = True


class CategorieFactory(DjangoModelFactory):
    class Meta:
        model = Categorie
        django_get_or_create = ("nom",)

    nom = factory.Sequence(lambda n: f"Categorie_{n}")


class UniteFactory(DjangoModelFactory):
    class Meta:
        model = Unite
        django_get_or_create = ("nom",)

    nom = factory.Sequence(lambda n: f"Unite_{n}")


class FournisseurFactory(DjangoModelFactory):
    class Meta:
        model = Fournisseur

    code = factory.Sequence(lambda n: n + 1)
    nom = factory.Sequence(lambda n: f"Fournisseur {n}")
    email = factory.Sequence(lambda n: f"fournisseur{n}@test.com")
    adresse = "123 Rue Test"
    telephone = "0000000000"
    ville = "Kinshasa"
    pays = "RDC"
    tuteur = "Tuteur Test"
    rccm = factory.Sequence(lambda n: f"RCCM{n:04d}")
    id_nat = factory.Sequence(lambda n: f"IDNAT{n:04d}")
    impot = "0"
    tva = "0"
    is_system = False
    actif = True
    type_frais = None


class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = Article

    code = factory.Sequence(lambda n: n + 1)
    designation = factory.Sequence(lambda n: f"Article {n}")
    description = "Description test"
    categorie = factory.SubFactory(CategorieFactory)
    unite = factory.SubFactory(UniteFactory)
    fournisseur = factory.SubFactory(FournisseurFactory)
    prix_achat = Decimal("100.00")
    prix_vente = Decimal("120.00")
    prix_vente_gros = Decimal("110.00")
    devise = "$"
    seuil = 10
    seuil_gros = 50
    emplacement = "A1"
    actif = True


class DetailsFactureFactory(DjangoModelFactory):
    class Meta:
        model = DetailsFacture

    facture = factory.SubFactory(FactureFactory)
    article = factory.SubFactory(ArticleFactory)
    qte = 1
    prix = Decimal("120.00")


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = Client

    code = factory.Sequence(lambda n: 3000 + n)
    nom = factory.Sequence(lambda n: f"Client {n}")
    email = factory.Sequence(lambda n: f"client{n}@test.com")
    adresse = "Adresse Test"
    telephone = "0000000000"
    ville = "Kinshasa"


class FactureClientFactory(DjangoModelFactory):
    class Meta:
        model = FactureClient

    facture = factory.SubFactory(FactureFactory)
    client = factory.SubFactory(ClientFactory)
