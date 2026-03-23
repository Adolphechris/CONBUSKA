"""
commandes/tests/factories.py

Factories factory-boy pour les tests du module commandes.
Un seul fichier partagé par tous les tests du module.
"""

import factory
from decimal import Decimal
from factory.django import DjangoModelFactory

from parametres.models import Devise
from produits.models import Article, Categorie, Unite
from fournisseurs.models import Fournisseur
from users.models import CustomUser
from commandes.models import Commande, DetailsCommande


class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    is_active = True
    type_profile = None


class DeviseFactory(DjangoModelFactory):
    class Meta:
        model = Devise
        django_get_or_create = ('code',)

    code = factory.Sequence(lambda n: f"D{n:02d}")
    nom = factory.LazyAttribute(lambda o: f"Devise {o.code}")
    symbole = factory.LazyAttribute(lambda o: o.code[:2])
    actif = True


class CategorieFactory(DjangoModelFactory):
    class Meta:
        model = Categorie
        django_get_or_create = ('nom',)

    nom = factory.Sequence(lambda n: f"Categorie_{n}")


class UniteFactory(DjangoModelFactory):
    class Meta:
        model = Unite
        django_get_or_create = ('nom',)

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
    prix_achat = Decimal('100.00')
    prix_vente = Decimal('120.00')
    prix_vente_gros = Decimal('110.00')
    devise = '$'
    seuil = 10
    seuil_gros = 50
    emplacement = "A1"
    actif = True


class CommandeFactory(DjangoModelFactory):
    class Meta:
        model = Commande

    numero = factory.Sequence(lambda n: 260001 + n)
    date_commande = factory.LazyFunction(
        lambda: __import__('datetime').date.today()
    )
    fournisseur = factory.SubFactory(FournisseurFactory)
    devise = factory.SubFactory(DeviseFactory)
    taux = Decimal('1.0000')
    cree_par = factory.SubFactory(CustomUserFactory)
    actif = True


class DetailsCommandeFactory(DjangoModelFactory):
    class Meta:
        model = DetailsCommande

    commande = factory.SubFactory(CommandeFactory)
    article = factory.SubFactory(ArticleFactory)
    qte = 5
    prix = Decimal('100.00')
