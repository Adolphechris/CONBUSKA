"""
produits/inputs.py

Dataclasses d'entrée pour les services du module produits.
Validation des données uniquement — aucune logique métier.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TransfertCreateInput:
    """Données nécessaires à la création d'un transfert de stock."""

    magasin_source_id: int
    magasin_destination_id: int


@dataclass(frozen=True)
class TransfertLigneAddInput:
    """Données pour ajouter (ou fusionner) une ligne dans un transfert."""

    transfert_id: int
    article_id: int
    qte: int


@dataclass(frozen=True)
class TransfertLigneUpdateInput:
    """Données pour modifier la quantité d'une ligne existante."""

    detail_id: int
    transfert_id: int  # vérifie l'appartenance au bon transfert
    qte: int
