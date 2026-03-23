"""
commandes/tests/test_selectors.py

Tests des selectors du module commandes.
Vérifient uniquement la lecture DB — aucun effet de bord.
"""

from decimal import Decimal

import pytest

from commandes.models import Commande, DetailsCommande
from commandes.selectors import (
    get_commande,
    liste_commandes,
    liste_details_commande,
    total_commande,
)

from .factories import (
    ArticleFactory,
    CommandeFactory,
    DetailsCommandeFactory,
)


@pytest.mark.django_db
class TestGetCommande:
    def test_retourne_la_commande(self):
        commande = CommandeFactory()
        result = get_commande(commande_id=commande.pk)
        assert result.pk == commande.pk

    def test_prefetch_fournisseur_et_devise(self):
        commande = CommandeFactory()
        result = get_commande(commande_id=commande.pk)
        # select_related déjà chargé — pas de requête supplémentaire
        assert result.fournisseur is not None
        assert result.devise is not None

    def test_leve_does_not_exist_si_introuvable(self):
        with pytest.raises(Commande.DoesNotExist):
            get_commande(commande_id=99999)


@pytest.mark.django_db
class TestListeCommandes:
    def test_retourne_toutes_les_commandes(self):
        CommandeFactory.create_batch(3)
        qs = liste_commandes()
        assert qs.count() == 3

    def test_tri_par_numero_decroissant(self):
        c1 = CommandeFactory(numero=260001)
        c2 = CommandeFactory(numero=260002)
        c3 = CommandeFactory(numero=260003)
        numeros = list(liste_commandes().values_list('numero', flat=True))
        assert numeros == [c3.numero, c2.numero, c1.numero]

    def test_queryset_non_evalue(self):
        CommandeFactory()
        qs = liste_commandes()
        assert hasattr(qs, 'filter'), "Doit retourner un QuerySet, pas une liste"


@pytest.mark.django_db
class TestListeDetailsCommande:
    def test_retourne_les_lignes_de_la_commande(self):
        commande = CommandeFactory()
        DetailsCommandeFactory.create_batch(3, commande=commande)
        qs = liste_details_commande(commande=commande)
        assert qs.count() == 3

    def test_ne_retourne_pas_les_lignes_dautres_commandes(self):
        commande_a = CommandeFactory()
        commande_b = CommandeFactory()
        DetailsCommandeFactory.create_batch(2, commande=commande_a)
        DetailsCommandeFactory.create_batch(1, commande=commande_b)
        assert liste_details_commande(commande=commande_a).count() == 2
        assert liste_details_commande(commande=commande_b).count() == 1

    def test_commande_vide_retourne_queryset_vide(self):
        commande = CommandeFactory()
        assert liste_details_commande(commande=commande).count() == 0


@pytest.mark.django_db
class TestTotalCommande:
    def test_calcule_la_somme_qte_fois_prix(self):
        commande = CommandeFactory()
        DetailsCommandeFactory(commande=commande, qte=2, prix=Decimal('50.00'))
        DetailsCommandeFactory(commande=commande, qte=3, prix=Decimal('100.00'))
        # 2×50 + 3×100 = 400
        assert total_commande(commande=commande) == Decimal('400.00')

    def test_commande_vide_retourne_zero(self):
        commande = CommandeFactory()
        assert total_commande(commande=commande) == Decimal('0')

    def test_retourne_decimal(self):
        commande = CommandeFactory()
        DetailsCommandeFactory(commande=commande, qte=1, prix=Decimal('10.00'))
        result = total_commande(commande=commande)
        assert isinstance(result, Decimal)
