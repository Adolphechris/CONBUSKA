"""
paie/selectors.py

Toute la logique de lecture/requête DB du module paie.
Aucun effet de bord. Keyword-only args systématiques.
"""

from datetime import date
from decimal import Decimal

from django.db.models import QuerySet, Sum

from caisse.models import MouvementCaisseAgent
from paie.models import Agent, LignePaie, Paie


# ── Utilitaire interne ────────────────────────────────────────────────────────

def _debut_fin_mois(mois: date) -> tuple[date, date]:
    """Retourne (1er du mois, 1er du mois suivant) pour les filtres de plage."""
    debut = mois.replace(day=1)
    if mois.month == 12:
        fin = date(mois.year + 1, 1, 1)
    else:
        fin = date(mois.year, mois.month + 1, 1)
    return debut, fin


# ── Agent ─────────────────────────────────────────────────────────────────────

def get_agent(*, agent_id: int) -> Agent:
    """Lève Agent.DoesNotExist si introuvable."""
    return Agent.objects.get(pk=agent_id)


def liste_agents(*, actif: bool | None = None) -> QuerySet[Agent]:
    """QuerySet non évalué. Filtre optionnel sur l'état actif."""
    qs = Agent.objects.all()
    if actif is not None:
        qs = qs.filter(actif=actif)
    return qs


def existe_agent_par_matricule(
    *,
    matricule: int,
    exclude_id: int | None = None,
) -> bool:
    """True si un agent avec ce matricule existe (optionnellement hors exclude_id)."""
    qs = Agent.objects.filter(matricule=matricule)
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


# ── Paie ──────────────────────────────────────────────────────────────────────

def get_paie(*, paie_id: int) -> Paie:
    """Lève Paie.DoesNotExist si introuvable."""
    return Paie.objects.select_related('agent', 'cree_par').get(pk=paie_id)


def liste_paies(
    *,
    mois: date | None = None,
    agent_id: int | None = None,
) -> QuerySet[Paie]:
    """QuerySet non évalué. Filtres optionnels sur le mois et l'agent."""
    qs = Paie.objects.select_related('agent')
    if mois is not None:
        debut, fin = _debut_fin_mois(mois)
        qs = qs.filter(mois__gte=debut, mois__lt=fin)
    if agent_id is not None:
        qs = qs.filter(agent_id=agent_id)
    return qs


def existe_paie(*, agent_id: int, mois: date) -> bool:
    """True si une paie existe déjà pour cet agent et ce mois (normalisé au 1er)."""
    mois_normalise = mois.replace(day=1)
    return Paie.objects.filter(agent_id=agent_id, mois=mois_normalise).exists()


def liste_lignes_paie(*, paie_id: int) -> QuerySet[LignePaie]:
    """QuerySet non évalué des lignes d'un bulletin, triées par ordre."""
    return LignePaie.objects.filter(paie_id=paie_id)


# ── Caisse ────────────────────────────────────────────────────────────────────

def cumul_caisse_par_rubrique(*, agent_id: int, mois: date) -> dict[str, Decimal]:
    """
    Retourne le total des mouvements caisse de l'agent pour le mois donné,
    regroupé par nom de rubrique.

    Utilisé par creer_paie pour calculer primes et retenues depuis la caisse.
    Les clés absentes indiquent un montant nul pour cette rubrique.
    """
    debut, fin = _debut_fin_mois(mois)
    rows = (
        MouvementCaisseAgent.objects
        .filter(
            agent_id=agent_id,
            mouvement_caisse__date_mouvement__date__gte=debut,
            mouvement_caisse__date_mouvement__date__lt=fin,
        )
        .values('mouvement_caisse__rubrique__nom')
        .annotate(total=Sum('mouvement_caisse__montant'))
    )
    return {
        row['mouvement_caisse__rubrique__nom']: row['total'] or Decimal('0')
        for row in rows
    }
