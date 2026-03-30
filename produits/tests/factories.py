"""
produits/tests/factories.py

Factories factory-boy pour les tests du module produits.
Un seul fichier partagé par tous les tests du module.
"""

import datetime

import factory
from factory.django import DjangoModelFactory

from parametres.models import Magasin
from produits.models import (
    Article,
    Categorie,
    DetailsTransfertStock,
    ReservationTransfertLot,
    Stock,
    TransfertStock,
    Unite,
)
from users.models import CustomUser


class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_produits_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True
    type_profile = None


class MagasinFactory(DjangoModelFactory):
    class Meta:
        model = Magasin

    nom = factory.Sequence(lambda n: f"Magasin {n}")
    description = "Description test"
    localisation = "Kinshasa"
    is_principal = False


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


class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = Article

    # code est généré dans save() mais on le fournit explicitement
    # pour éviter le select_for_update() qui requiert une transaction.
    code = factory.Sequence(lambda n: 9000 + n)
    designation = factory.Sequence(lambda n: f"Article produits {n}")
    description = "Description test"
    categorie = factory.SubFactory(CategorieFactory)
    unite = factory.SubFactory(UniteFactory)
    fournisseur = None
    prix_achat = 100
    prix_vente = 120
    prix_vente_gros = 110
    devise = "FC"
    seuil = 5
    seuil_gros = 20
    emplacement = "A1"
    actif = True


class StockFactory(DjangoModelFactory):
    class Meta:
        model = Stock

    magasin = factory.SubFactory(MagasinFactory)
    article = factory.SubFactory(ArticleFactory)
    qte = 100
    date_peremption = factory.LazyFunction(
        lambda: datetime.date.today().replace(year=datetime.date.today().year + 1)
    )


class TransfertStockFactory(DjangoModelFactory):
    class Meta:
        model = TransfertStock

    # numero est généré dans save() — fourni explicitement pour les tests
    numero = factory.Sequence(lambda n: 260001 + n)
    magasin_source = factory.SubFactory(MagasinFactory)
    magasin_destination = factory.SubFactory(MagasinFactory)
    cree_par = factory.SubFactory(CustomUserFactory)
    actif = True
    valide = False


class DetailsTransfertStockFactory(DjangoModelFactory):
    class Meta:
        model = DetailsTransfertStock

    transfert = factory.SubFactory(TransfertStockFactory)
    article = factory.SubFactory(ArticleFactory)
    qte = 10


class ReservationTransfertLotFactory(DjangoModelFactory):
    class Meta:
        model = ReservationTransfertLot

    transfert = factory.SubFactory(TransfertStockFactory)
    article = factory.SubFactory(ArticleFactory)
    date_peremption = factory.LazyFunction(
        lambda: datetime.date.today().replace(year=datetime.date.today().year + 1)
    )
    qte = 10
