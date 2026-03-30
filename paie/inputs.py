"""
paie/inputs.py

Dataclasses d'entrée des services du module paie.
Validées en amont dans les Django Forms avant construction.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from paie.models import TypeContrat


@dataclass(frozen=True)
class AgentCreateInput:
    nom: str
    date_naissance: date
    date_engagement: date
    adresse: str
    telephone: str
    ville: str
    salaire: Decimal
    poste: str = ""
    departement: str = ""
    type_contrat: str = TypeContrat.CDI
    email: str | None = None


@dataclass(frozen=True)
class AgentUpdateInput:
    agent_id: int
    nom: str
    date_naissance: date
    date_engagement: date
    adresse: str
    telephone: str
    ville: str
    salaire: Decimal
    poste: str = ""
    departement: str = ""
    type_contrat: str = TypeContrat.CDI
    email: str | None = None


@dataclass(frozen=True)
class PaieCreateInput:
    agent_id: int
    mois: date              # normalisé au 1er du mois dans le service
    jap: int = 26           # jours ouvrables du mois
    jp: int = 26            # jours payés
    absence: int = 0
