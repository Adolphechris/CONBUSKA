"""
produits/tests/test_services.py

Tests des services du module produits — transferts de stock.
"""

import datetime

import pytest

from produits.exceptions import (
    ReservationVideError,
    StockInsuffisantError,
    TransfertDejaValideError,
    TransfertInactifError,
    TransfertNonValideError,
)
from produits.inputs import (
    TransfertCreateInput,
    TransfertLigneAddInput,
    TransfertLigneUpdateInput,
)
from produits.models import (
    DetailsTransfertStock,
    MouvementStock,
    ReservationTransfertLot,
)
from produits.services.transfert_service import (
    ajouter_ligne_transfert,
    annuler_transfert,
    creer_transfert,
    modifier_ligne_transfert,
    supprimer_ligne_transfert,
    valider_transfert,
)
from produits.tests.factories import (
    ArticleFactory,
    CustomUserFactory,
    DetailsTransfertStockFactory,
    MagasinFactory,
    ReservationTransfertLotFactory,
    StockFactory,
    TransfertStockFactory,
)


# ── creer_transfert ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_creer_transfert_nominal():
    user = CustomUserFactory()
    source = MagasinFactory()
    dest = MagasinFactory()

    data = TransfertCreateInput(
        magasin_source_id=source.pk,
        magasin_destination_id=dest.pk,
    )
    result = creer_transfert(data=data, current_user=user)

    assert result.transfert.pk is not None
    assert result.transfert.magasin_source_id == source.pk
    assert result.transfert.magasin_destination_id == dest.pk
    assert result.transfert.cree_par_id == user.pk
    assert result.transfert.valide is False
    assert result.transfert.actif is True


@pytest.mark.django_db
def test_creer_transfert_attribue_un_numero():
    user = CustomUserFactory()
    source = MagasinFactory()
    dest = MagasinFactory()

    data = TransfertCreateInput(
        magasin_source_id=source.pk,
        magasin_destination_id=dest.pk,
    )
    result = creer_transfert(data=data, current_user=user)

    assert result.transfert.numero is not None
    assert result.transfert.numero > 0


@pytest.mark.django_db
def test_creer_transfert_numeros_incrementaux():
    user = CustomUserFactory()
    source = MagasinFactory()
    dest = MagasinFactory()
    data = TransfertCreateInput(
        magasin_source_id=source.pk, magasin_destination_id=dest.pk
    )

    r1 = creer_transfert(data=data, current_user=user)
    r2 = creer_transfert(data=data, current_user=user)

    assert r2.transfert.numero == r1.transfert.numero + 1


# ── ajouter_ligne_transfert ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_ajouter_ligne_transfert_nominal():
    magasin = MagasinFactory()
    article = ArticleFactory()
    peremption = datetime.date.today() + datetime.timedelta(days=365)
    StockFactory(magasin=magasin, article=article, qte=20, date_peremption=peremption)
    transfert = TransfertStockFactory(magasin_source=magasin)

    data = TransfertLigneAddInput(
        transfert_id=transfert.pk,
        article_id=article.pk,
        qte=5,
    )
    result = ajouter_ligne_transfert(data=data)

    assert result.detail.article_id == article.pk
    assert result.detail.qte == 5
    assert result.transfert.pk == transfert.pk

    reservations = ReservationTransfertLot.objects.filter(transfert=transfert)
    assert reservations.count() == 1
    assert reservations.first().qte == 5


@pytest.mark.django_db
def test_ajouter_ligne_transfert_fusionne_si_article_existant():
    magasin = MagasinFactory()
    article = ArticleFactory()
    peremption = datetime.date.today() + datetime.timedelta(days=365)
    StockFactory(magasin=magasin, article=article, qte=50, date_peremption=peremption)
    transfert = TransfertStockFactory(magasin_source=magasin)

    data = TransfertLigneAddInput(
        transfert_id=transfert.pk, article_id=article.pk, qte=5
    )
    ajouter_ligne_transfert(data=data)
    ajouter_ligne_transfert(data=data)

    assert DetailsTransfertStock.objects.filter(transfert=transfert).count() == 1
    detail = DetailsTransfertStock.objects.get(transfert=transfert)
    assert detail.qte == 10  # 5 + 5 fusionnés


@pytest.mark.django_db
def test_ajouter_ligne_transfert_leve_si_transfert_inactif():
    magasin = MagasinFactory()
    article = ArticleFactory()
    StockFactory(magasin=magasin, article=article, qte=20)
    transfert = TransfertStockFactory(magasin_source=magasin, actif=False)

    data = TransfertLigneAddInput(
        transfert_id=transfert.pk, article_id=article.pk, qte=5
    )
    with pytest.raises(TransfertInactifError):
        ajouter_ligne_transfert(data=data)


@pytest.mark.django_db
def test_ajouter_ligne_transfert_leve_si_stock_insuffisant():
    magasin = MagasinFactory()
    article = ArticleFactory()
    StockFactory(magasin=magasin, article=article, qte=2)
    transfert = TransfertStockFactory(magasin_source=magasin)

    data = TransfertLigneAddInput(
        transfert_id=transfert.pk, article_id=article.pk, qte=10
    )
    with pytest.raises(StockInsuffisantError):
        ajouter_ligne_transfert(data=data)


@pytest.mark.django_db
def test_ajouter_ligne_transfert_recalcule_reservations():
    """Ajouter une seconde fois le même article repart des réservations à zéro."""
    magasin = MagasinFactory()
    article = ArticleFactory()
    peremption = datetime.date.today() + datetime.timedelta(days=365)
    StockFactory(magasin=magasin, article=article, qte=50, date_peremption=peremption)
    transfert = TransfertStockFactory(magasin_source=magasin)

    data5 = TransfertLigneAddInput(
        transfert_id=transfert.pk, article_id=article.pk, qte=5
    )
    data3 = TransfertLigneAddInput(
        transfert_id=transfert.pk, article_id=article.pk, qte=3
    )
    ajouter_ligne_transfert(data=data5)
    ajouter_ligne_transfert(data=data3)

    # Les réservations doivent refléter la quantité totale (5 + 3 = 8)
    total_reserve = sum(
        r.qte
        for r in ReservationTransfertLot.objects.filter(
            transfert=transfert, article=article
        )
    )
    assert total_reserve == 8


# ── modifier_ligne_transfert ────────────────────────────────────────────────────

@pytest.mark.django_db
def test_modifier_ligne_transfert_nominal():
    magasin = MagasinFactory()
    article = ArticleFactory()
    peremption = datetime.date.today() + datetime.timedelta(days=365)
    StockFactory(magasin=magasin, article=article, qte=20, date_peremption=peremption)
    transfert = TransfertStockFactory(magasin_source=magasin)
    detail = DetailsTransfertStockFactory(
        transfert=transfert, article=article, qte=5
    )
    ReservationTransfertLotFactory(
        transfert=transfert, article=article, date_peremption=peremption, qte=5
    )

    data = TransfertLigneUpdateInput(
        detail_id=detail.pk,
        transfert_id=transfert.pk,
        qte=12,
    )
    result = modifier_ligne_transfert(data=data)

    detail.refresh_from_db()
    assert detail.qte == 12
    assert result.detail.qte == 12

    total_reserve = sum(
        r.qte
        for r in ReservationTransfertLot.objects.filter(
            transfert=transfert, article=article
        )
    )
    assert total_reserve == 12


@pytest.mark.django_db
def test_modifier_ligne_transfert_leve_si_mauvais_transfert():
    """La ligne doit appartenir au transfert indiqué dans l'input."""
    magasin = MagasinFactory()
    article = ArticleFactory()
    autre_transfert = TransfertStockFactory(magasin_source=magasin)
    detail = DetailsTransfertStockFactory(
        transfert=autre_transfert, article=article, qte=5
    )
    bon_transfert = TransfertStockFactory(magasin_source=magasin)

    data = TransfertLigneUpdateInput(
        detail_id=detail.pk,
        transfert_id=bon_transfert.pk,  # mauvais transfert
        qte=3,
    )
    from produits.models import DetailsTransfertStock
    with pytest.raises(DetailsTransfertStock.DoesNotExist):
        modifier_ligne_transfert(data=data)


@pytest.mark.django_db
def test_modifier_ligne_transfert_leve_si_inactif():
    magasin = MagasinFactory()
    article = ArticleFactory()
    transfert = TransfertStockFactory(magasin_source=magasin, actif=False)
    detail = DetailsTransfertStockFactory(
        transfert=transfert, article=article, qte=5
    )

    data = TransfertLigneUpdateInput(
        detail_id=detail.pk, transfert_id=transfert.pk, qte=3
    )
    with pytest.raises(TransfertInactifError):
        modifier_ligne_transfert(data=data)


@pytest.mark.django_db
def test_modifier_ligne_transfert_leve_si_stock_insuffisant():
    magasin = MagasinFactory()
    article = ArticleFactory()
    StockFactory(magasin=magasin, article=article, qte=3)
    transfert = TransfertStockFactory(magasin_source=magasin)
    detail = DetailsTransfertStockFactory(
        transfert=transfert, article=article, qte=2
    )

    data = TransfertLigneUpdateInput(
        detail_id=detail.pk, transfert_id=transfert.pk, qte=10
    )
    with pytest.raises(StockInsuffisantError):
        modifier_ligne_transfert(data=data)


# ── supprimer_ligne_transfert ───────────────────────────────────────────────────

@pytest.mark.django_db
def test_supprimer_ligne_transfert_nominal():
    magasin = MagasinFactory()
    article = ArticleFactory()
    peremption = datetime.date.today() + datetime.timedelta(days=365)
    transfert = TransfertStockFactory(magasin_source=magasin)
    detail = DetailsTransfertStockFactory(
        transfert=transfert, article=article, qte=5
    )
    ReservationTransfertLotFactory(
        transfert=transfert, article=article, date_peremption=peremption, qte=5
    )

    returned_transfert = supprimer_ligne_transfert(detail_id=detail.pk)

    assert returned_transfert.pk == transfert.pk
    assert not DetailsTransfertStock.objects.filter(pk=detail.pk).exists()
    assert not ReservationTransfertLot.objects.filter(
        transfert=transfert, article=article
    ).exists()


@pytest.mark.django_db
def test_supprimer_ligne_transfert_supprime_reservations_de_cet_article_uniquement():
    """Les réservations d'autres articles ne doivent pas être supprimées."""
    magasin = MagasinFactory()
    a1 = ArticleFactory()
    a2 = ArticleFactory()
    peremption = datetime.date.today() + datetime.timedelta(days=365)
    transfert = TransfertStockFactory(magasin_source=magasin)

    detail1 = DetailsTransfertStockFactory(transfert=transfert, article=a1, qte=5)
    DetailsTransfertStockFactory(transfert=transfert, article=a2, qte=3)
    ReservationTransfertLotFactory(
        transfert=transfert, article=a1, date_peremption=peremption, qte=5
    )
    ReservationTransfertLotFactory(
        transfert=transfert, article=a2, date_peremption=peremption, qte=3
    )

    supprimer_ligne_transfert(detail_id=detail1.pk)

    assert not ReservationTransfertLot.objects.filter(
        transfert=transfert, article=a1
    ).exists()
    assert ReservationTransfertLot.objects.filter(
        transfert=transfert, article=a2
    ).exists()


@pytest.mark.django_db
def test_supprimer_ligne_transfert_leve_si_inactif():
    transfert = TransfertStockFactory(actif=False)
    detail = DetailsTransfertStockFactory(transfert=transfert)

    with pytest.raises(TransfertInactifError):
        supprimer_ligne_transfert(detail_id=detail.pk)


# ── valider_transfert ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_valider_transfert_nominal():
    magasin_source = MagasinFactory()
    magasin_dest = MagasinFactory()
    article = ArticleFactory()
    peremption = datetime.date.today() + datetime.timedelta(days=365)

    StockFactory(
        magasin=magasin_source,
        article=article,
        qte=10,
        date_peremption=peremption,
    )
    transfert = TransfertStockFactory(
        magasin_source=magasin_source,
        magasin_destination=magasin_dest,
    )
    ReservationTransfertLotFactory(
        transfert=transfert,
        article=article,
        date_peremption=peremption,
        qte=5,
    )

    result = valider_transfert(transfert_id=transfert.pk)

    transfert.refresh_from_db()
    assert transfert.valide is True
    assert result.transfert.pk == transfert.pk

    # Vérifier les mouvements créés (1 OUT source + 1 IN destination)
    mvts = MouvementStock.objects.filter(
        source_type="TransfertStock",
        source_id=transfert.pk,
    )
    assert mvts.count() == 2
    assert mvts.filter(type=MouvementStock.OUT).count() == 1
    assert mvts.filter(type=MouvementStock.IN).count() == 1


@pytest.mark.django_db
def test_valider_transfert_leve_si_deja_valide():
    transfert = TransfertStockFactory(valide=True)

    with pytest.raises(TransfertDejaValideError):
        valider_transfert(transfert_id=transfert.pk)


@pytest.mark.django_db
def test_valider_transfert_leve_si_sans_reservations():
    transfert = TransfertStockFactory(valide=False)

    with pytest.raises(ReservationVideError):
        valider_transfert(transfert_id=transfert.pk)


# ── annuler_transfert ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_annuler_transfert_leve_si_non_valide():
    transfert = TransfertStockFactory(valide=False)

    with pytest.raises(TransfertNonValideError):
        annuler_transfert(transfert_id=transfert.pk)


@pytest.mark.django_db
def test_annuler_transfert_nominal():
    """Valider puis annuler remet valide=False et crée les compensatoires."""
    magasin_source = MagasinFactory()
    magasin_dest = MagasinFactory()
    article = ArticleFactory()
    peremption = datetime.date.today() + datetime.timedelta(days=365)

    StockFactory(
        magasin=magasin_source,
        article=article,
        qte=10,
        date_peremption=peremption,
    )
    transfert = TransfertStockFactory(
        magasin_source=magasin_source,
        magasin_destination=magasin_dest,
    )
    ReservationTransfertLotFactory(
        transfert=transfert,
        article=article,
        date_peremption=peremption,
        qte=5,
    )

    valider_transfert(transfert_id=transfert.pk)
    result = annuler_transfert(transfert_id=transfert.pk)

    transfert.refresh_from_db()
    assert transfert.valide is False
    assert result.transfert.pk == transfert.pk

    # Après annulation : 4 mouvements (2 originaux + 2 compensatoires)
    mvts = MouvementStock.objects.filter(
        source_type="TransfertStock",
        source_id=transfert.pk,
    )
    assert mvts.count() == 4
