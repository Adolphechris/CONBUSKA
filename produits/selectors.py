"""
produits/selectors.py

Selectors du module produits — lecture seule, aucun effet de bord.
Toutes les requêtes DB des transferts de stock passent ici.
"""

from django.db.models import Prefetch, QuerySet

from produits.models import (
    DetailsTransfertStock,
    ReservationTransfertLot,
    Stock,
    TransfertStock,
)


def get_transfert(*, transfert_id: int) -> TransfertStock:
    """Lève TransfertStock.DoesNotExist si introuvable."""
    return (
        TransfertStock.objects
        .select_related("magasin_source", "magasin_destination", "cree_par")
        .get(pk=transfert_id)
    )


def liste_transferts() -> QuerySet[TransfertStock]:
    """Tous les transferts, ordonnés du plus récent au plus ancien."""
    return (
        TransfertStock.objects
        .select_related("magasin_source", "magasin_destination", "cree_par")
        .order_by("-date_creation")
    )


def get_detail_transfert(*, detail_id: int) -> DetailsTransfertStock:
    """Lève DetailsTransfertStock.DoesNotExist si introuvable."""
    return (
        DetailsTransfertStock.objects
        .select_related("article", "transfert")
        .get(pk=detail_id)
    )


def liste_details_transfert(*, transfert_id: int) -> QuerySet[DetailsTransfertStock]:
    """
    Lignes d'un transfert avec article et lots réservés pré-chargés.

    Les lots sont attachés via l'attribut `lots_reserves` sur le transfert,
    compatible avec DetailsTransfertStock.get_my_lots().
    """
    reservations_qs = ReservationTransfertLot.objects.order_by("date_peremption")
    return (
        DetailsTransfertStock.objects
        .filter(transfert_id=transfert_id)
        .select_related("article", "transfert")
        .prefetch_related(
            Prefetch(
                "transfert__reservationtransfertlot_set",
                queryset=reservations_qs,
                to_attr="lots_reserves",
            )
        )
        .order_by("article")
    )


def liste_reservations_transfert(
    *, transfert_id: int
) -> QuerySet[ReservationTransfertLot]:
    """Réservations d'un transfert, ordonnées FIFO (date_peremption ASC)."""
    return (
        ReservationTransfertLot.objects
        .filter(transfert_id=transfert_id)
        .select_related("article")
        .order_by("date_peremption")
    )


def liste_lots_disponibles(
    *, magasin_id: int, article_id: int
) -> QuerySet[Stock]:
    """
    Lots avec stock positif pour un article et un magasin donnés.
    Ordonnés FIFO (date_peremption ASC) — prêts pour la réservation.
    """
    return (
        Stock.objects
        .filter(magasin_id=magasin_id, article_id=article_id, qte__gt=0)
        .order_by("date_peremption")
    )
