"""
factures/tests/test_services.py

Tests de la logique métier — FactureService.
"""

import pytest
from django.core.exceptions import ValidationError

from factures.exceptions import ClientComptorManquantError
from factures.services import FactureService
from factures.tests.factories import (
    ClientFactory,
    CustomUserFactory,
    DetailsFactureFactory,
    FactureClientFactory,
    FactureFactory,
)


@pytest.mark.django_db
def test_valider_sans_beneficiaire_leve_erreur():
    """
    Cas d'erreur : facture sans client_comptoir ni FactureClient → ClientComptorManquantError.
    """
    user = CustomUserFactory()
    facture = FactureFactory(client_comptoir=None)
    DetailsFactureFactory(facture=facture)

    with pytest.raises(ClientComptorManquantError) as exc_info:
        FactureService.valider(facture=facture, user=user)

    assert "obligatoire" in str(exc_info.value)


@pytest.mark.django_db
def test_valider_avec_client_comptoir_franchit_la_garde():
    """
    Cas nominal : client_comptoir renseigné → la garde est franchie.
    L'exception levée ensuite provient du magasin absent, pas de la garde.
    """
    user = CustomUserFactory()
    facture = FactureFactory(client_comptoir="Jean Dupont")
    DetailsFactureFactory(facture=facture)

    with pytest.raises(Exception) as exc_info:
        FactureService.valider(facture=facture, user=user)

    assert not isinstance(exc_info.value, ClientComptorManquantError)


@pytest.mark.django_db
def test_valider_avec_facture_client_franchit_la_garde():
    """
    Cas nominal : FactureClient associée → la garde est franchie même sans client_comptoir.
    """
    user = CustomUserFactory()
    client = ClientFactory()
    facture = FactureFactory(client_comptoir=None)
    DetailsFactureFactory(facture=facture)
    FactureClientFactory(facture=facture, client=client)

    with pytest.raises(Exception) as exc_info:
        FactureService.valider(facture=facture, user=user)

    assert not isinstance(exc_info.value, ClientComptorManquantError)


@pytest.mark.django_db
def test_valider_facture_sans_articles_leve_validation_error():
    """
    Garde existante préservée : une facture vide (aucun article) lève ValidationError,
    indépendamment du client_comptoir.
    """
    user = CustomUserFactory()
    facture = FactureFactory(client_comptoir="Client test")

    with pytest.raises(ValidationError):
        FactureService.valider(facture=facture, user=user)


@pytest.mark.django_db
def test_valider_facture_deja_validee_leve_validation_error():
    """
    Garde existante préservée : double validation lève ValidationError.
    """
    user = CustomUserFactory()
    facture = FactureFactory(client_comptoir="Client test", valide=True)

    with pytest.raises(ValidationError):
        FactureService.valider(facture=facture, user=user)
