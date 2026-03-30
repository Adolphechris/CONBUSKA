"""
produits/services/transfert_service.py

Services du module produits — transferts de stock.
Toute la logique métier des transferts passe ici.
Aucune logique dans les views, aucune requête directe hors selectors.
"""

import datetime
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Max

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
    Stock,
    TransfertStock,
)
from produits.services.stock_service import StockService


# ── Output dataclasses ──────────────────────────────────────────────────────────

@dataclass
class TransfertResult:
    transfert: TransfertStock


@dataclass
class LigneResult:
    detail: DetailsTransfertStock
    transfert: TransfertStock


# ── Helpers privés ──────────────────────────────────────────────────────────────

def _get_prochain_numero() -> int:
    """
    Calcule le prochain numéro de transfert avec un verrou exclusif.
    Doit être appelé à l'intérieur d'une transaction atomique.
    """
    last = TransfertStock.objects.select_for_update().aggregate(Max("numero"))["numero__max"]
    return (last + 1) if last else int(datetime.datetime.now().strftime("%y") + "0000")


@transaction.atomic
def _reserver_lots_fifo(
    *, transfert: TransfertStock, article, qte: int
) -> None:
    """
    Réserve le stock lot par lot (FIFO) pour un article et un transfert.

    Lit le snapshot Stock avec select_for_update() pour bloquer les
    réservations concurrentes. Lève StockInsuffisantError si le stock
    de la source est insuffisant.
    """
    lots = (
        Stock.objects
        .select_for_update()
        .filter(
            magasin=transfert.magasin_source,
            article=article,
            qte__gt=0,
        )
        .order_by("date_peremption")
    )

    reste = qte
    reservations = []

    for lot in lots:
        if reste <= 0:
            break
        consomme = min(lot.qte, reste)
        reservations.append(
            ReservationTransfertLot(
                transfert=transfert,
                article=article,
                date_peremption=lot.date_peremption,
                qte=consomme,
            )
        )
        reste -= consomme

    if reste > 0:
        raise StockInsuffisantError(
            f"Stock insuffisant pour « {article} » dans « {transfert.magasin_source} » "
            f"(manque {reste} unité(s))."
        )

    ReservationTransfertLot.objects.bulk_create(reservations)


# ── Services publics ────────────────────────────────────────────────────────────

@transaction.atomic
def creer_transfert(
    *, data: TransfertCreateInput, current_user
) -> TransfertResult:
    """Crée un nouveau transfert de stock en brouillon."""
    transfert = TransfertStock.objects.create(
        magasin_source_id=data.magasin_source_id,
        magasin_destination_id=data.magasin_destination_id,
        cree_par=current_user,
    )
    return TransfertResult(transfert=transfert)


@transaction.atomic
def ajouter_ligne_transfert(*, data: TransfertLigneAddInput) -> LigneResult:
    """
    Ajoute une ligne au transfert, ou fusionne la quantité si l'article
    est déjà présent. Recalcule les réservations FIFO pour l'article.

    Lève TransfertInactifError si le transfert est inactif.
    Lève StockInsuffisantError si le stock source est insuffisant.
    """
    transfert = TransfertStock.objects.select_for_update().get(pk=data.transfert_id)

    if not transfert.actif:
        raise TransfertInactifError(
            "Ce transfert est inactif et ne peut plus être modifié."
        )

    detail, created = DetailsTransfertStock.objects.get_or_create(
        transfert=transfert,
        article_id=data.article_id,
        defaults={"qte": data.qte},
    )
    if not created:
        detail.qte += data.qte
        detail.save(update_fields=["qte"])

    # Recalculer les réservations pour cet article depuis zéro
    ReservationTransfertLot.objects.filter(
        transfert=transfert,
        article_id=data.article_id,
    ).delete()

    _reserver_lots_fifo(
        transfert=transfert,
        article=detail.article,
        qte=detail.qte,
    )

    return LigneResult(detail=detail, transfert=transfert)


@transaction.atomic
def modifier_ligne_transfert(*, data: TransfertLigneUpdateInput) -> LigneResult:
    """
    Modifie la quantité d'une ligne existante.

    Vérifie que la ligne appartient bien au transfert indiqué (sécurité).
    Recalcule les réservations FIFO pour l'article.

    Lève DetailsTransfertStock.DoesNotExist si la ligne n'appartient pas
    au transfert ou si elle est introuvable.
    Lève TransfertInactifError si le transfert est inactif.
    Lève StockInsuffisantError si le stock source est insuffisant.
    """
    detail = (
        DetailsTransfertStock.objects
        .select_related("article", "transfert")
        .select_for_update()
        .get(pk=data.detail_id, transfert_id=data.transfert_id)
    )
    transfert = detail.transfert

    if not transfert.actif:
        raise TransfertInactifError(
            "Ce transfert est inactif et ne peut plus être modifié."
        )

    detail.qte = data.qte
    detail.save(update_fields=["qte"])

    ReservationTransfertLot.objects.filter(
        transfert=transfert,
        article=detail.article,
    ).delete()

    _reserver_lots_fifo(
        transfert=transfert,
        article=detail.article,
        qte=detail.qte,
    )

    return LigneResult(detail=detail, transfert=transfert)


@transaction.atomic
def supprimer_ligne_transfert(*, detail_id: int) -> TransfertStock:
    """
    Supprime une ligne de transfert et toutes ses réservations associées.
    Retourne le transfert parent.

    Lève TransfertInactifError si le transfert est inactif.
    """
    detail = (
        DetailsTransfertStock.objects
        .select_related("transfert", "article")
        .select_for_update()
        .get(pk=detail_id)
    )
    transfert = detail.transfert

    if not transfert.actif:
        raise TransfertInactifError(
            "Ce transfert est inactif et ne peut plus être modifié."
        )

    ReservationTransfertLot.objects.filter(
        transfert=transfert,
        article=detail.article,
    ).delete()

    detail.delete()

    return transfert


@transaction.atomic
def valider_transfert(*, transfert_id: int) -> TransfertResult:
    """
    Exécute les mouvements de stock correspondant aux réservations.

    Idempotence : lève TransfertDejaValideError si le transfert est déjà validé
    (select_for_update() prévient la double validation concurrente).
    Lève ReservationVideError si aucune réservation n'est enregistrée.
    """
    transfert = TransfertStock.objects.select_for_update().get(pk=transfert_id)

    if transfert.valide:
        raise TransfertDejaValideError("Ce transfert est déjà validé.")

    reservations = (
        ReservationTransfertLot.objects
        .select_related("article")
        .filter(transfert=transfert)
        .order_by("date_peremption")
    )

    if not reservations.exists():
        raise ReservationVideError(
            "Ce transfert ne contient aucune réservation. "
            "Ajoutez au moins un article avant de valider."
        )

    for r in reservations:
        StockService.sortir_stock_lot(
            magasin=transfert.magasin_source,
            article=r.article,
            date_peremption=r.date_peremption,
            qte=r.qte,
            source=transfert,
        )
        StockService.entrer_stock(
            magasin=transfert.magasin_destination,
            article=r.article,
            qte=r.qte,
            date_peremption=r.date_peremption,
            source=transfert,
        )

    transfert.valide = True
    transfert.save(update_fields=["valide"])

    return TransfertResult(transfert=transfert)


@transaction.atomic
def annuler_transfert(*, transfert_id: int) -> TransfertResult:
    """
    Annule un transfert validé en inversant tous ses mouvements de stock.

    Lève TransfertNonValideError si le transfert n'est pas encore validé.
    """
    transfert = TransfertStock.objects.select_for_update().get(pk=transfert_id)

    if not transfert.valide:
        raise TransfertNonValideError("Seul un transfert validé peut être annulé.")

    mvts = MouvementStock.objects.filter(
        source_type=transfert.__class__.__name__,
        source_id=transfert.pk,
    )
    for mvt in mvts:
        StockService.annuler_mouvement(mvt)

    transfert.valide = False
    transfert.save(update_fields=["valide"])

    return TransfertResult(transfert=transfert)
