"""
commandes/exceptions.py

Exceptions métier de l'application commandes.
"""


class CommandeError(Exception):
    """Exception de base pour l'application commandes."""


class CommandeDejaClotureError(CommandeError):
    """
    Levée quand on tente de clôturer ou d'annuler une commande
    qui est déjà inactive (actif=False).
    """


class CommandeArticleDuplicatError(CommandeError):
    """
    Levée si la logique de fusion de doublon échoue de façon inattendue.
    En pratique, les doublons sont fusionnés silencieusement — cette
    exception sert de filet de sécurité.
    """


class CommandeNonValideeError(CommandeError):
    """
    Levée quand on tente de transformer une commande qui n'est pas validée.
    """
