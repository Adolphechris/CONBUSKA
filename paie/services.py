"""
paie/services.py

Toute la logique métier du module paie.
Transactions, effets de bord, intégration caisse.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Max

from caisse.models import (
    CaisseCourante,
    MouvementCaisse,
    MouvementCaisseAgent,
    RubriqueCaisse,
)
from paie.constants import RubriquePaie
from paie.exceptions import (
    AgentInactifError,
    CaissePrincipaleFermeeError,
    PaieDejaExistanteError,
    PaieDejaValideeError,
)
from paie.inputs import AgentCreateInput, AgentUpdateInput, PaieCreateInput
from paie.models import Agent, LignePaie, Paie, TypeLigne
from paie.selectors import cumul_caisse_par_rubrique, existe_paie
from users.models import CustomUser


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    agent: Agent


@dataclass
class PaieResult:
    paie: Paie


@dataclass
class PaieValidationResult:
    paie: Paie
    mouvement_caisse_cree: bool
    warning: str | None = None


# ── Utilitaires internes ──────────────────────────────────────────────────────

def _get_prochain_matricule() -> int:
    """
    Génère le prochain matricule en verrouillant la ligne avec le max.
    Doit être appelé à l'intérieur d'une transaction atomique.
    """
    last = (
        Agent.objects
        .select_for_update()
        .order_by('-matricule')
        .values_list('matricule', flat=True)
        .first()
    )
    return (last or 0) + 1


def _quantize(montant: Decimal) -> Decimal:
    return montant.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# ── Agent ─────────────────────────────────────────────────────────────────────

@transaction.atomic
def creer_agent(*, data: AgentCreateInput, current_user: CustomUser) -> AgentResult:
    """Crée un nouvel agent avec matricule auto-incrémenté."""
    matricule = _get_prochain_matricule()
    agent = Agent.objects.create(
        matricule=matricule,
        nom=data.nom,
        date_naissance=data.date_naissance,
        date_engagement=data.date_engagement,
        adresse=data.adresse,
        telephone=data.telephone,
        ville=data.ville,
        salaire=data.salaire,
        poste=data.poste,
        departement=data.departement,
        type_contrat=data.type_contrat,
        email=data.email or None,
        actif=True,
    )
    return AgentResult(agent=agent)


@transaction.atomic
def modifier_agent(*, data: AgentUpdateInput, current_user: CustomUser) -> AgentResult:
    """Modifie les informations d'un agent existant."""
    agent = Agent.objects.select_for_update().get(pk=data.agent_id)
    agent.nom = data.nom
    agent.date_naissance = data.date_naissance
    agent.date_engagement = data.date_engagement
    agent.adresse = data.adresse
    agent.telephone = data.telephone
    agent.ville = data.ville
    agent.salaire = data.salaire
    agent.poste = data.poste
    agent.departement = data.departement
    agent.type_contrat = data.type_contrat
    agent.email = data.email or None
    agent.save(update_fields=[
        'nom', 'date_naissance', 'date_engagement', 'adresse',
        'telephone', 'ville', 'salaire', 'poste', 'departement',
        'type_contrat', 'email', 'date_modification',
    ])
    return AgentResult(agent=agent)


@transaction.atomic
def desactiver_agent(*, agent_id: int, current_user: CustomUser) -> AgentResult:
    """Désactive logiquement un agent (actif=False)."""
    agent = Agent.objects.select_for_update().get(pk=agent_id)
    if not agent.actif:
        raise AgentInactifError(f"L'agent {agent.nom} est déjà inactif.")
    agent.actif = False
    agent.save(update_fields=['actif', 'date_modification'])
    return AgentResult(agent=agent)


# ── Paie ──────────────────────────────────────────────────────────────────────

@transaction.atomic
def creer_paie(*, data: PaieCreateInput, current_user: CustomUser) -> PaieResult:
    """
    Crée un bulletin de paie pour un agent.

    Calcule les montants depuis les mouvements caisse du mois,
    crée les lignes de détail et enregistre les snapshots.

    Formule :
        salaire_brut   = salaire_base × (jp / jap)
        total_primes   = Σ LignePaie[type=GAIN] (hors salaire_base)
        total_retenues = Σ LignePaie[type=RETENUE]
        net_a_payer    = salaire_brut + total_primes − total_retenues
    """
    mois = data.mois.replace(day=1)

    if existe_paie(agent_id=data.agent_id, mois=mois):
        raise PaieDejaExistanteError(
            f"Une paie existe déjà pour ce mois ({mois.strftime('%m/%Y')})."
        )

    agent = Agent.objects.select_for_update().get(pk=data.agent_id)

    if not agent.actif:
        raise AgentInactifError(
            f"Impossible de créer une paie pour l'agent inactif {agent.nom}."
        )

    # ── Calcul du salaire brut (prorata jours payés / jours ouvrables) ────
    salaire_base = agent.salaire
    jap = data.jap or 26
    jp = data.jp if data.jp is not None else jap
    absence = data.absence

    salaire_brut = _quantize(salaire_base * jp / jap)

    # ── Cumuls caisse du mois pour cet agent ─────────────────────────────
    cumuls = cumul_caisse_par_rubrique(agent_id=agent.pk, mois=mois)

    transport    = _quantize(cumuls.get(RubriquePaie.TRANSPORT, Decimal('0')))
    restauration = _quantize(cumuls.get(RubriquePaie.RESTAURATION, Decimal('0')))
    assistance   = _quantize(cumuls.get(RubriquePaie.ASSISTANCE, Decimal('0')))
    avance       = _quantize(cumuls.get(RubriquePaie.AVANCE_SALAIRE, Decimal('0')))

    total_primes   = transport + restauration + assistance
    total_retenues = avance
    net_a_payer    = salaire_brut + total_primes - total_retenues

    # ── Création de la Paie ───────────────────────────────────────────────
    paie = Paie.objects.create(
        agent=agent,
        mois=mois,
        salaire_base=salaire_base,
        jap=jap,
        jp=jp,
        absence=absence,
        salaire_brut=salaire_brut,
        total_primes=total_primes,
        total_retenues=total_retenues,
        net_a_payer=net_a_payer,
        valide=False,
        cree_par=current_user,
    )

    # ── Création des lignes de détail ────────────────────────────────────
    lignes = [
        LignePaie(
            paie=paie,
            libelle=RubriquePaie.SALAIRE_BASE,
            type_ligne=TypeLigne.GAIN,
            montant=salaire_brut,
            ordre=0,
        ),
    ]
    ordre_prime = 1
    for libelle, montant in (
        (RubriquePaie.TRANSPORT,    transport),
        (RubriquePaie.RESTAURATION, restauration),
        (RubriquePaie.ASSISTANCE,   assistance),
    ):
        if montant > 0:
            lignes.append(LignePaie(
                paie=paie,
                libelle=libelle,
                type_ligne=TypeLigne.GAIN,
                montant=montant,
                ordre=ordre_prime,
            ))
            ordre_prime += 1

    if avance > 0:
        lignes.append(LignePaie(
            paie=paie,
            libelle=RubriquePaie.AVANCE_SALAIRE,
            type_ligne=TypeLigne.RETENUE,
            montant=avance,
            ordre=10,
        ))

    LignePaie.objects.bulk_create(lignes)

    return PaieResult(paie=paie)


@transaction.atomic
def supprimer_paie(*, paie_id: int, current_user: CustomUser) -> None:
    """
    Supprime physiquement un bulletin de paie non validé.
    Supprime d'abord les LignePaie (FK PROTECT) avant la Paie.
    """
    paie = Paie.objects.select_for_update().get(pk=paie_id)
    if paie.valide:
        raise PaieDejaValideeError(
            "Impossible de supprimer un bulletin déjà validé."
        )
    paie.lignes.all().delete()
    paie.delete()


@transaction.atomic
def valider_paie(*, paie_id: int, current_user: CustomUser) -> PaieValidationResult:
    """
    Valide un bulletin de paie et crée le mouvement caisse correspondant.

    Le mouvement « Solde sur salaire » est créé de façon idempotente :
    s'il existe déjà pour cet agent et ce mois, aucun doublon n'est créé
    et un avertissement est retourné.

    Le montant du mouvement = net_a_payer (snapshot).
    """
    paie = Paie.objects.select_for_update().get(pk=paie_id)

    if paie.valide:
        raise PaieDejaValideeError(
            f"La paie de {paie.agent} ({paie.mois.strftime('%m/%Y')}) est déjà validée."
        )

    # ── Vérification idempotence (mouvement déjà créé manuellement) ───────
    mois = paie.mois  # déjà normalisé au 1er
    if mois.month == 12:
        fin_mois = date(mois.year + 1, 1, 1)
    else:
        fin_mois = date(mois.year, mois.month + 1, 1)

    mouvement_existant = MouvementCaisseAgent.objects.filter(
        agent=paie.agent,
        mouvement_caisse__rubrique__nom=RubriquePaie.SOLDE_SALAIRE,
        mouvement_caisse__date_mouvement__date__gte=mois,
        mouvement_caisse__date_mouvement__date__lt=fin_mois,
    ).exists()

    warning: str | None = None
    mouvement_caisse_cree = False

    if mouvement_existant:
        warning = (
            "Un mouvement « Solde sur salaire » existe déjà en caisse "
            "pour ce mois — aucun doublon créé."
        )
    else:
        # ── Récupération de la caisse principale ouverte ──────────────────
        try:
            caisse_courante = CaisseCourante.objects.get(
                caisse__is_principal=True,
                est_ouverte=True,
            )
        except CaisseCourante.DoesNotExist:
            raise CaissePrincipaleFermeeError(
                "Aucune caisse principale ouverte — impossible de valider la paie."
            )

        rubrique = RubriqueCaisse.objects.get(nom=RubriquePaie.SOLDE_SALAIRE)

        mouvement = MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement='SORTIE',
            rubrique=rubrique,
            montant=paie.net_a_payer,
            motif=(
                f"Salaire {paie.agent} — {paie.mois.strftime('%m/%Y')}"
            ),
            effectue_par=current_user,
        )
        MouvementCaisseAgent.objects.create(
            mouvement_caisse=mouvement,
            agent=paie.agent,
        )
        mouvement_caisse_cree = True

    # ── Validation du bulletin ────────────────────────────────────────────
    paie.valide = True
    paie.modifie_par = current_user
    paie.save(update_fields=['valide', 'modifie_par', 'date_modification'])

    return PaieValidationResult(
        paie=paie,
        mouvement_caisse_cree=mouvement_caisse_cree,
        warning=warning,
    )
