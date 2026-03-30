"""
paie/tests/factories.py

Factories factory-boy pour les tests du module paie.
Un seul fichier partagé par tous les tests du module.
"""

import datetime
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from caisse.models import (
    Caisse,
    CaisseCourante,
    MouvementCaisse,
    MouvementCaisseAgent,
    RubriqueCaisse,
)
from paie.models import Agent, LignePaie, Paie, TypeContrat, TypeLigne
from users.models import CustomUser


class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_paie_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    is_active = True
    type_profile = None


class AgentFactory(DjangoModelFactory):
    class Meta:
        model = Agent

    matricule = factory.Sequence(lambda n: n + 1)
    nom = factory.Sequence(lambda n: f"Agent {n}")
    date_naissance = datetime.date(1990, 1, 1)
    date_engagement = datetime.date(2020, 1, 1)
    adresse = "123 Avenue Test"
    telephone = "0000000000"
    ville = "Kinshasa"
    poste = "Développeur"
    departement = "Informatique"
    type_contrat = TypeContrat.CDI
    salaire = Decimal('1500.00')
    actif = True
    email = factory.Sequence(lambda n: f"agent{n}@test.com")


class PaieFactory(DjangoModelFactory):
    class Meta:
        model = Paie

    agent = factory.SubFactory(AgentFactory)
    mois = datetime.date(2026, 1, 1)
    salaire_base = Decimal('1500.00')
    jap = 26
    jp = 26
    absence = 0
    salaire_brut = Decimal('1500.00')
    total_primes = Decimal('0.00')
    total_retenues = Decimal('0.00')
    net_a_payer = Decimal('1500.00')
    valide = False
    cree_par = factory.SubFactory(CustomUserFactory)


class LignePaieFactory(DjangoModelFactory):
    class Meta:
        model = LignePaie

    paie = factory.SubFactory(PaieFactory)
    libelle = "Salaire de base"
    type_ligne = TypeLigne.GAIN
    montant = Decimal('1500.00')
    ordre = 0


# ── Factories caisse (pour intégration valider_paie / creer_paie) ─────────────

class CaisseFactory(DjangoModelFactory):
    class Meta:
        model = Caisse

    nom = factory.Sequence(lambda n: f"Caisse {n}")
    is_principal = True


class CaisseCouranteFactory(DjangoModelFactory):
    class Meta:
        model = CaisseCourante

    caisse = factory.SubFactory(CaisseFactory)
    ouvert_par = factory.SubFactory(CustomUserFactory)
    solde_initial = Decimal('10000.00')
    est_ouverte = True


class RubriqueCaisseFactory(DjangoModelFactory):
    class Meta:
        model = RubriqueCaisse
        django_get_or_create = ('nom',)

    nom = factory.Sequence(lambda n: f"Rubrique {n}")
    description = "Description test"
    visible = True


class MouvementCaisseFactory(DjangoModelFactory):
    class Meta:
        model = MouvementCaisse

    caisse = factory.SubFactory(CaisseCouranteFactory)
    type_mouvement = 'SORTIE'
    rubrique = factory.SubFactory(RubriqueCaisseFactory)
    montant = Decimal('100.00')
    motif = "Mouvement test"
    effectue_par = factory.SubFactory(CustomUserFactory)


class MouvementCaisseAgentFactory(DjangoModelFactory):
    class Meta:
        model = MouvementCaisseAgent

    mouvement_caisse = factory.SubFactory(MouvementCaisseFactory)
    agent = factory.SubFactory(AgentFactory)
