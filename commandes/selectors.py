"""
commandes/selectors.py

Toute la logique de lecture DB du module commandes.
Aucun effet de bord. Aucune écriture.
"""

from decimal import Decimal

from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    QuerySet,
    Subquery,
    Sum,
)

from .models import Commande, DetailsCommande


def get_commande(*, commande_id: int) -> Commande:
    """Lève Commande.DoesNotExist si introuvable."""
    return (
        Commande.objects
        .select_related('fournisseur', 'devise')
        .get(id=commande_id)
    )


def liste_commandes() -> QuerySet[Commande]:
    """
    Toutes les commandes, triées par numéro décroissant.
    Annotées avec `total_commande` (Sum qte×prix) pour la liste.
    """
    total_subq = (
        DetailsCommande.objects
        .filter(commande=OuterRef('pk'))
        .values('commande')
        .annotate(
            t=Sum(
                ExpressionWrapper(
                    F('qte') * F('prix'),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
        )
        .values('t')
    )
    return (
        Commande.objects
        .select_related('fournisseur', 'devise')
        .annotate(
            total_commande=Subquery(
                total_subq,
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        .order_by('-numero')
    )


def liste_details_commande(*, commande: Commande) -> QuerySet[DetailsCommande]:
    """Lignes d'une commande, triées par ordre d'insertion."""
    return (
        DetailsCommande.objects
        .filter(commande=commande)
        .select_related('article', 'article__unite')
        .order_by('pk')
    )


def total_commande(*, commande: Commande) -> Decimal:
    """
    Somme de (qte × prix) sur toutes les lignes de la commande.
    Retourne Decimal('0') si la commande est vide.
    Remplace Commande.total_commande (ancienne @property avec requête DB).
    """
    result = (
        DetailsCommande.objects
        .filter(commande=commande)
        .aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('qte') * F('prix'),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
        )
    )
    return result['total'] or Decimal('0')
