"""
parametres/exceptions.py

Exceptions métier de l'application parametres.
RateNotFoundError est importée par caisse — elle vit ici car TauxEchange
est défini dans parametres.
"""


class ParametresException(Exception):
    """Exception de base pour l'application parametres."""
    pass


class RateNotFoundError(ParametresException):
    """
    Aucun taux de change valide pour la paire de devises et la date demandées.
    Levée par TauxEchangeManager.get_rate_for_date() quand aucun enregistrement
    avec effective_date <= date n'existe pour la paire (source, cible).
    """
    pass