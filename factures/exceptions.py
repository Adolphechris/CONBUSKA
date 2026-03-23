"""
factures/exceptions.py

Exceptions métier de l'application factures.
"""


class FactureError(Exception):
    """Exception de base pour l'application factures."""


class ClientComptorManquantError(FactureError):
    """
    Levée lorsqu'une facture ordinaire est validée sans client_comptoir
    et sans FactureClient associée.
    """
