"""
produits/tests/test_selectors.py

Tests des selectors du module produits.
"""

import datetime

import pytest

from produits.models import DetailsTransfertStock, TransfertStock
from produits.selectors import (
    get_detail_transfert,
    get_transfert,
    liste_details_transfert,
    liste_lots_disponibles,
    liste_reservations_transfert,
    liste_transferts,
)
from produits.tests.factories import (
    ArticleFactory,
    DetailsTransfertStockFactory,
    MagasinFactory,
    ReservationTransfertLotFactory,
    StockFactory,
    TransfertStockFactory,
)


# ── get_transfert ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_get_transfert_nominal():
    transfert = TransfertStockFactory()
    result = get_transfert(transfert_id=transfert.pk)
    assert result.pk == transfert.pk


@pytest.mark.django_db
def test_get_transfert_leve_does_not_exist():
    with pytest.raises(TransfertStock.DoesNotExist):
        get_transfert(transfert_id=99999)


@pytest.mark.django_db
def test_get_transfert_select_related_ne_genere_pas_de_requetes_supplementaires(
    django_assert_num_queries,
):
    transfert = TransfertStockFactory()
    with django_assert_num_queries(1):
        t = get_transfert(transfert_id=transfert.pk)
        # accès aux FK select_related — pas de requête supplémentaire
        _ = t.magasin_source.nom
        _ = t.magasin_destination.nom
        _ = t.cree_par.username


# ── liste_transferts ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_liste_transferts_retourne_tous():
    TransfertStockFactory.create_batch(3)
    qs = liste_transferts()
    assert qs.count() == 3


@pytest.mark.django_db
def test_liste_transferts_ordre_decroissant():
    t1 = TransfertStockFactory()
    t2 = TransfertStockFactory()
    pks = list(liste_transferts().values_list("pk", flat=True))
    # t2 créé après t1 → doit apparaître en premier
    assert pks.index(t2.pk) < pks.index(t1.pk)


@pytest.mark.django_db
def test_liste_transferts_vide():
    assert liste_transferts().count() == 0


# ── get_detail_transfert ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_get_detail_transfert_nominal():
    detail = DetailsTransfertStockFactory()
    result = get_detail_transfert(detail_id=detail.pk)
    assert result.pk == detail.pk


@pytest.mark.django_db
def test_get_detail_transfert_leve_does_not_exist():
    with pytest.raises(DetailsTransfertStock.DoesNotExist):
        get_detail_transfert(detail_id=99999)


# ── liste_details_transfert ────────────────────────────────────────────────────

@pytest.mark.django_db
def test_liste_details_transfert_filtre_par_transfert():
    transfert = TransfertStockFactory()
    autre = TransfertStockFactory()
    DetailsTransfertStockFactory.create_batch(2, transfert=transfert)
    DetailsTransfertStockFactory(transfert=autre)

    qs = liste_details_transfert(transfert_id=transfert.pk)
    assert qs.count() == 2
    assert all(d.transfert_id == transfert.pk for d in qs)


@pytest.mark.django_db
def test_liste_details_transfert_vide():
    transfert = TransfertStockFactory()
    assert liste_details_transfert(transfert_id=transfert.pk).count() == 0


@pytest.mark.django_db
def test_liste_details_transfert_prefetch_lots(django_assert_num_queries):
    transfert = TransfertStockFactory()
    article = ArticleFactory()
    DetailsTransfertStockFactory(transfert=transfert, article=article)
    ReservationTransfertLotFactory(transfert=transfert, article=article)

    # 1 requête principale (select_related article + transfert) + 1 prefetch reservations
    with django_assert_num_queries(2):
        details = list(liste_details_transfert(transfert_id=transfert.pk))
        for d in details:
            # accès via get_my_lots() sans requête supplémentaire
            _ = d.get_my_lots()


# ── liste_reservations_transfert ───────────────────────────────────────────────

@pytest.mark.django_db
def test_liste_reservations_transfert_filtre_par_transfert():
    transfert = TransfertStockFactory()
    autre = TransfertStockFactory()
    article = ArticleFactory()
    ReservationTransfertLotFactory.create_batch(3, transfert=transfert, article=article)
    ReservationTransfertLotFactory(transfert=autre, article=article)

    qs = liste_reservations_transfert(transfert_id=transfert.pk)
    assert qs.count() == 3
    assert all(r.transfert_id == transfert.pk for r in qs)


@pytest.mark.django_db
def test_liste_reservations_transfert_ordre_fifo():
    transfert = TransfertStockFactory()
    article = ArticleFactory()
    today = datetime.date.today()
    r_tard = ReservationTransfertLotFactory(
        transfert=transfert, article=article,
        date_peremption=today + datetime.timedelta(days=60),
    )
    r_tot = ReservationTransfertLotFactory(
        transfert=transfert, article=article,
        date_peremption=today + datetime.timedelta(days=10),
    )
    pks = list(
        liste_reservations_transfert(transfert_id=transfert.pk)
        .values_list("pk", flat=True)
    )
    assert pks[0] == r_tot.pk   # date_peremption la plus proche en premier
    assert pks[1] == r_tard.pk


@pytest.mark.django_db
def test_liste_reservations_transfert_vide():
    transfert = TransfertStockFactory()
    assert liste_reservations_transfert(transfert_id=transfert.pk).count() == 0


# ── liste_lots_disponibles ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_liste_lots_disponibles_exclut_stock_nul():
    magasin = MagasinFactory()
    article = ArticleFactory()
    StockFactory(magasin=magasin, article=article, qte=50)
    StockFactory(
        magasin=magasin, article=article, qte=0,
        date_peremption=datetime.date.today() + datetime.timedelta(days=200),
    )
    qs = liste_lots_disponibles(magasin_id=magasin.pk, article_id=article.pk)
    assert qs.count() == 1
    assert qs.first().qte == 50


@pytest.mark.django_db
def test_liste_lots_disponibles_filtre_par_magasin_et_article():
    magasin = MagasinFactory()
    autre_magasin = MagasinFactory()
    article = ArticleFactory()
    autre_article = ArticleFactory()
    StockFactory(magasin=magasin, article=article, qte=10)
    StockFactory(magasin=autre_magasin, article=article, qte=10)
    StockFactory(magasin=magasin, article=autre_article, qte=10)

    qs = liste_lots_disponibles(magasin_id=magasin.pk, article_id=article.pk)
    assert qs.count() == 1


@pytest.mark.django_db
def test_liste_lots_disponibles_ordre_fifo():
    magasin = MagasinFactory()
    article = ArticleFactory()
    today = datetime.date.today()
    lot_tard = StockFactory(
        magasin=magasin, article=article, qte=10,
        date_peremption=today + datetime.timedelta(days=90),
    )
    lot_tot = StockFactory(
        magasin=magasin, article=article, qte=10,
        date_peremption=today + datetime.timedelta(days=10),
    )
    pks = list(
        liste_lots_disponibles(magasin_id=magasin.pk, article_id=article.pk)
        .values_list("pk", flat=True)
    )
    assert pks[0] == lot_tot.pk   # péremption la plus proche en premier
    assert pks[1] == lot_tard.pk


@pytest.mark.django_db
def test_liste_lots_disponibles_vide():
    magasin = MagasinFactory()
    article = ArticleFactory()
    qs = liste_lots_disponibles(magasin_id=magasin.pk, article_id=article.pk)
    assert qs.count() == 0
