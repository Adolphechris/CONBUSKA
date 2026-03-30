"""
paie/exceptions.py

Exceptions métier du module paie.
"""


class PaieError(Exception):
    """Base pour toutes les exceptions du module paie."""


class AgentDejaExisteError(PaieError):
    """Matricule ou nom déjà utilisé par un autre agent."""


class AgentInactifError(PaieError):
    """Action refusée sur un agent inactif."""


class PaieDejaExistanteError(PaieError):
    """Une paie existe déjà pour cet agent et ce mois."""


class PaieDejaValideeError(PaieError):
    """Paie déjà validée — suppression ou modification impossible."""


class CaissePrincipaleFermeeError(PaieError):
    """Aucune caisse principale ouverte pour enregistrer le mouvement."""
