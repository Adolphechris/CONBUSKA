"""
produits/exceptions.py

Exceptions métier du module produits (transferts de stock).
"""


class TransfertError(Exception):
    """Base pour toutes les exceptions métier des transferts."""


class TransfertDejaValideError(TransfertError):
    """Levée si on tente de valider un transfert déjà validé."""


class TransfertNonValideError(TransfertError):
    """Levée si on tente d'annuler un transfert qui n'est pas encore validé."""


class TransfertInactifError(TransfertError):
    """Levée si on tente de modifier un transfert inactif (actif=False)."""


class StockInsuffisantError(TransfertError):
    """Levée quand le stock source est insuffisant pour couvrir la réservation."""


class ReservationVideError(TransfertError):
    """Levée si on valide un transfert sans aucune réservation existante."""
