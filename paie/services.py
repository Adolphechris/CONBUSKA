"""
paie/services.py

Logique métier du module paie.
Calcul des bulletins, primes, retenues, cotisations sociales.
"""

from decimal import Decimal
from datetime import date
from typing import List, Dict, Optional

from django.db import transaction
from django.utils import timezone

from users.models import CustomUser
from parametres.models import get_taux_usd_cdf

from .models import Agent, Paie, LignePaie, TypeLigne
from .exceptions import (
    AgentInactifError,
    PaieDejaValideeError,
    PaieDejaExistanteError,
    CaissePrincipaleFermeeError,
)


# ── Dataclasses ───────────────────────────────────────────────────────────────

class PaieResult:
    def __init__(self, paie: Paie):
        self.paie = paie


class LignePaieResult:
    def __init__(self, ligne: LignePaie):
        self.ligne = ligne


# ── Helpers ───────────────────────────────────────────────────────────────────

def _calculer_cnss(salaire_brut: Decimal) -> Decimal:
    """
    Calcule la cotisation CNSS (employé + employeur).
    
    Taux CNSS RDC 2024 :
    - Employé : 5% du salaire brut (plafond 500 000 FC)
    - Employeur : 10% du salaire brut (plafond 500 000 FC)
    
    Pour simplifier, on ne garde que la part employé (déduite du net).
    """
    plafond = Decimal('500000')
    taux_employe = Decimal('0.05')
    
    base_cnss = min(salaire_brut, plafond)
    return base_cnss * taux_employe


def _calculer_ipr(salaire_net_avant_impot: Decimal) -> Decimal:
    """
    Calcule l'impôt professionnel (IPR) selon le barème RDC 2024.
    
    Barème mensuel (FC) :
    - 0 à 30 000 : 0%
    - 30 001 à 60 000 : 5% sur la part > 30 000
    - 60 001 à 120 000 : 10% sur la part > 60 000 + 1 500
    - 120 001 à 200 000 : 15% sur la part > 120 000 + 6 500
    - > 200 000 : 20% sur la part > 200 000 + 16 500
    """
    if salaire_net_avant_impot <= Decimal('30000'):
        return Decimal('0')
    elif salaire_net_avant_impot <= Decimal('60000'):
        return (salaire_net_avant_impot - Decimal('30000')) * Decimal('0.05')
    elif salaire_net_avant_impot <= Decimal('120000'):
        return (salaire_net_avant_impot - Decimal('60000')) * Decimal('0.10') + Decimal('1500')
    elif salaire_net_avant_impot <= Decimal('200000'):
        return (salaire_net_avant_impot - Decimal('120000')) * Decimal('0.15') + Decimal('6500')
    else:
        return (salaire_net_avant_impot - Decimal('200000')) * Decimal('0.20') + Decimal('16500')


def _calculer_prime_anciennete(agent: Agent, salaire_base: Decimal) -> Decimal:
    """
    Calcule la prime d'ancienneté.
    
    Règles :
    - 1 à 5 ans : 2% par année
    - 6 à 10 ans : 3% par année
    - > 10 ans : 5% par année
    """
    date_engagement = agent.date_engagement
    aujourd_hui = timezone.now().date()
    
    annees = aujourd_hui.year - date_engagement.year
    if (aujourd_hui.month, aujourd_hui.day) < (date_engagement.month, date_engagement.day):
        annees -= 1
    
    if annees <= 0:
        return Decimal('0')
    elif annees <= 5:
        taux = Decimal('0.02') * annees
    elif annees <= 10:
        taux = Decimal('0.03') * annees
    else:
        taux = Decimal('0.05') * annees
    
    return salaire_base * taux


def _generer_matricule() -> int:
    """Génère un matricule unique pour un nouvel agent (max+1 ou 1)."""
    last = Agent.objects.order_by('matricule').last()
    return (last.matricule + 1) if last else 1


# ── Services ──────────────────────────────────────────────────────────────────

@transaction.atomic
def calculer_bulletin(
    *,
    agent_id: int,
    mois: date,
    current_user: CustomUser,
    jp: Optional[int] = None,
    absence: int = 0,
    lignes_supplementaires: Optional[List[Dict]] = None,
) -> PaieResult:
    """
    Calcule et crée un bulletin de paie pour un agent.
    
    Args:
        agent_id: ID de l'agent
        mois: Date du mois (normalisé au 1er du mois)
        current_user: Utilisateur qui crée le bulletin
        jp: Jours payés (défaut: jap - absence)
        absence: Jours d'absence
        lignes_supplementaires: Liste de lignes additionnelles
    
    Returns:
        PaieResult avec le bulletin créé
    """
    agent = Agent.objects.get(id=agent_id)
    
    # Normaliser le mois au 1er du mois
    mois_normalise = mois.replace(day=1)
    
    # Vérifier si l'agent est actif
    if not agent.actif:
        raise AgentInactifError(f"L'agent {agent.nom} est inactif.")
    
    # Vérifier si un bulletin existe déjà pour ce mois
    existing = Paie.objects.filter(agent=agent, mois=mois_normalise).first()
    if existing:
        raise PaieDejaExistanteError(
            f"Un bulletin existe déjà pour {agent.nom} en {mois.strftime('%m/%Y')}"
        )
    
    # Récupérer le taux USD
    taux_usd = get_taux_usd_cdf(mois_normalise)
    
    # Calculs de base
    salaire_base = agent.salaire
    jap = 26  # Jours ouvrables par défaut
    if jp is None:
        jp = jap - absence
    else:
        jp = min(jp, jap)
    
    # Salaire brut au prorata
    salaire_brut = salaire_base * Decimal(jp) / Decimal(jap)
    
    # Primes et retenues (initialisation)
    total_primes = Decimal('0')
    total_retenues = Decimal('0')
    
    # Récupérer les mouvements caisse liés à l'agent pour ce mois
    from caisse.models import MouvementCaisseAgent
    mouvements_agent = MouvementCaisseAgent.objects.filter(
        agent=agent
    ).select_related('mouvement_caisse').prefetch_related('mouvement_caisse__rubrique')
    
    lignes_primes = []
    lignes_retenues = []
    
    for mv_agent in mouvements_agent:
        mv = mv_agent.mouvement_caisse
        if mv.date_mouvement and mv.date_mouvement.date().replace(day=1) != mois_normalise:
            continue
        
        montant = Decimal(str(mv.montant))
        rubrique = mv.rubrique
        
        if mv.type_mouvement == 'ENTREE':
            total_primes += montant
            lignes_primes.append((rubrique.nom if rubrique else 'Prime', montant))
        elif mv.type_mouvement == 'SORTIE':
            total_retenues += montant
            lignes_retenues.append((rubrique.nom if rubrique else 'Retenue', montant))
    
    # Retenues automatiques (CNSS + IPR) — désactivés par défaut
    # Les primes/retenues proviennent uniquement des mouvements caisse
    cnss = Decimal('0')
    ipr = Decimal('0')
    
    # Net à payer — plancher à 0 pour éviter solde négatif
    net_a_payer = max(Decimal('0'), salaire_brut + total_primes - total_retenues)
    
    # Créer le bulletin
    paie = Paie.objects.create(
        mois=mois_normalise,
        agent=agent,
        salaire_base=salaire_base,
        jap=jap,
        jp=jp,
        absence=absence,
        salaire_brut=salaire_brut,
        total_primes=total_primes,
        total_retenues=total_retenues,
        net_a_payer=net_a_payer,
        taux_creation=taux_usd,
        valeur_usd=net_a_payer / taux_usd if taux_usd > 0 else Decimal('0'),
        cree_par=current_user,
    )
    
    # Créer les lignes de paie
    lignes = []
    
    # Créer les lignes de paie
    lignes = []
    ordre = 1
    
    # Ligne salaire base
    lignes.append(LignePaie(
        paie=paie,
        libelle='Salaire de base',
        type_ligne=TypeLigne.GAIN,
        montant=salaire_brut,
        ordre=ordre,
        taux_creation=taux_usd,
        valeur_usd=salaire_brut / taux_usd if taux_usd > 0 else Decimal('0'),
    ))
    ordre += 1
    
    # Lignes primes (mouvements caisse ENTREE)
    for libelle, montant in lignes_primes:
        lignes.append(LignePaie(
            paie=paie,
            libelle=libelle,
            type_ligne=TypeLigne.GAIN,
            montant=montant,
            ordre=ordre,
            taux_creation=taux_usd,
            valeur_usd=montant / taux_usd if taux_usd > 0 else Decimal('0'),
        ))
        ordre += 1
    
    # Ligne CNSS
    if cnss > 0:
        lignes.append(LignePaie(
            paie=paie,
            libelle='CNSS (part employé)',
            type_ligne=TypeLigne.RETENUE,
            montant=cnss,
            ordre=ordre,
            taux_creation=taux_usd,
            valeur_usd=cnss / taux_usd if taux_usd > 0 else Decimal('0'),
        ))
        ordre += 1
    
    # Lignes retenues (mouvements caisse SORTIE)
    for libelle, montant in lignes_retenues:
        lignes.append(LignePaie(
            paie=paie,
            libelle=libelle,
            type_ligne=TypeLigne.RETENUE,
            montant=montant,
            ordre=ordre,
            taux_creation=taux_usd,
            valeur_usd=montant / taux_usd if taux_usd > 0 else Decimal('0'),
        ))
        ordre += 1
    
    # Ligne IPR
    if ipr > 0:
        lignes.append(LignePaie(
            paie=paie,
            libelle='IPR (Impôt professionnel)',
            type_ligne=TypeLigne.RETENUE,
            montant=ipr,
            ordre=ordre,
            taux_creation=taux_usd,
            valeur_usd=ipr / taux_usd if taux_usd > 0 else Decimal('0'),
        ))
        ordre += 1
    
    # Lignes supplémentaires
    if lignes_supplementaires:
        for idx, ligne_data in enumerate(lignes_supplementaires, start=200):
            montant = Decimal(str(ligne_data.get('montant', 0)))
            lignes.append(LignePaie(
                paie=paie,
                libelle=ligne_data.get('libelle', ''),
                type_ligne=ligne_data.get('type_ligne', TypeLigne.GAIN),
                montant=montant,
                ordre=idx,
                taux_creation=taux_usd,
                valeur_usd=montant / taux_usd if taux_usd > 0 else Decimal('0'),
            ))
    
    # Bulk create
    LignePaie.objects.bulk_create(lignes)
    
    return PaieResult(paie=paie)


@transaction.atomic
def valider_bulletin(
    *,
    paie_id: int,
    current_user: CustomUser,
) -> PaieResult:
    """
    Valide un bulletin de paie (bloque les modifications).
    """
    paie = Paie.objects.select_for_update().get(id=paie_id)
    
    if paie.valide:
        raise PaieDejaValideeError(f"Le bulletin de {paie.agent.nom} est déjà validé.")
    
    paie.valide = True
    paie.modifie_par = current_user
    paie.save(update_fields=['valide', 'modifie_par', 'date_modification'])
    
    return PaieResult(paie=paie)


@transaction.atomic
def supprimer_bulletin(
    *,
    paie_id: int,
    current_user: CustomUser,
) -> None:
    """
    Supprime un bulletin de paie (seulement si non validé).
    """
    paie = Paie.objects.select_for_update().get(id=paie_id)
    
    if paie.valide:
        raise PaieDejaValideeError("Impossible de supprimer un bulletin validé.")
    
    # Supprimer les lignes d'abord (PROTECT)
    LignePaie.objects.filter(paie=paie).delete()
    paie.delete()


@transaction.atomic
def ajouter_ligne_paie(
    *,
    paie_id: int,
    libelle: str,
    type_ligne: str,
    montant: Decimal,
    current_user: CustomUser,
) -> LignePaieResult:
    """
    Ajoute une ligne à un bulletin non validé.
    """
    paie = Paie.objects.select_for_update().get(id=paie_id)
    
    if paie.valide:
        raise ValueError("Impossible de modifier un bulletin validé.")
    
    taux_usd = paie.taux_creation or get_taux_usd_cdf()
    
    ligne = LignePaie.objects.create(
        paie=paie,
        libelle=libelle,
        type_ligne=type_ligne,
        montant=montant,
        ordre=LignePaie.objects.filter(paie=paie).count() + 1,
        taux_creation=taux_usd,
        valeur_usd=montant / taux_usd if taux_usd > 0 else Decimal('0'),
    )
    
    # Recalculer les totaux
    _recalculer_totaux(paie)
    
    return LignePaieResult(ligne=ligne)


@transaction.atomic
def modifier_ligne_paie(
    *,
    ligne_id: int,
    libelle: Optional[str] = None,
    montant: Optional[Decimal] = None,
    current_user: CustomUser,
) -> LignePaieResult:
    """
    Modifie une ligne de paie.
    """
    ligne = LignePaie.objects.select_for_update().get(id=ligne_id)
    
    if ligne.paie.valide:
        raise ValueError("Impossible de modifier un bulletin validé.")
    
    if libelle is not None:
        ligne.libelle = libelle
    if montant is not None:
        ligne.montant = montant
        taux_usd = ligne.taux_creation or get_taux_usd_cdf()
        ligne.valeur_usd = montant / taux_usd if taux_usd > 0 else Decimal('0')
    
    ligne.save()
    
    # Recalculer les totaux
    _recalculer_totaux(ligne.paie)
    
    return LignePaieResult(ligne=ligne)


@transaction.atomic
def supprimer_ligne_paie(
    *,
    ligne_id: int,
    current_user: CustomUser,
) -> None:
    """
    Supprime une ligne de paie.
    """
    ligne = LignePaie.objects.select_for_update().get(id=ligne_id)
    paie = ligne.paie
    
    if paie.valide:
        raise ValueError("Impossible de modifier un bulletin validé.")
    
    ligne.delete()
    
    # Recalculer les totaux
    _recalculer_totaux(paie)


def _recalculer_totaux(paie: Paie) -> None:
    """
    Recalcule les totaux du bulletin à partir des lignes.
    """
    lignes = LignePaie.objects.filter(paie=paie)
    
    total_primes = sum(
        l.montant for l in lignes if l.type_ligne == TypeLigne.GAIN
    )
    total_retenues = sum(
        l.montant for l in lignes if l.type_ligne == TypeLigne.RETENUE
    )
    
    # Salaire brut = salaire base proratisé
    salaire_brut = paie.salaire_base * Decimal(paie.jp) / Decimal(paie.jap)
    
    # Net à payer
    net_a_payer = salaire_brut + total_primes - total_retenues
    
    # Mettre à jour
    paie.salaire_brut = salaire_brut
    paie.total_primes = total_primes
    paie.total_retenues = total_retenues
    paie.net_a_payer = net_a_payer
    
    # Mettre à jour USD
    taux_usd = paie.taux_creation or get_taux_usd_cdf()
    paie.valeur_usd = net_a_payer / taux_usd if taux_usd > 0 else Decimal('0')
    
    paie.save(update_fields=[
        'salaire_brut', 'total_primes', 'total_retenues',
        'net_a_payer', 'valeur_usd', 'date_modification'
    ])


# ── Services existants (pour compatibilité avec les vues) ────────────────────

@transaction.atomic
def creer_agent(
    *,
    data: 'AgentCreateInput',
    current_user: CustomUser,
) -> 'AgentResult':
    """Crée un nouvel agent."""
    
    agent = Agent.objects.create(
        matricule=data.matricule or _generer_matricule(),
        nom=data.nom,
        date_naissance=data.date_naissance,
        date_engagement=data.date_engagement,
        adresse=data.adresse,
        telephone=data.telephone,
        ville=data.ville,
        salaire=data.salaire,
        poste=data.poste or '',
        departement=data.departement or '',
        type_contrat=data.type_contrat or 'CDI',
        email=data.email,
    )
    return AgentResult(agent=agent)


@transaction.atomic
def modifier_agent(
    *,
    data: 'AgentUpdateInput',
    current_user: CustomUser,
) -> 'AgentResult':
    """Modifie un agent existant."""
    
    agent = Agent.objects.select_for_update().get(id=data.agent_id)
    agent.nom = data.nom
    agent.date_naissance = data.date_naissance
    agent.date_engagement = data.date_engagement
    agent.adresse = data.adresse
    agent.telephone = data.telephone
    agent.ville = data.ville
    agent.salaire = data.salaire
    agent.poste = data.poste or ''
    agent.departement = data.departement or ''
    agent.type_contrat = data.type_contrat or 'CDI'
    agent.email = data.email
    agent.save()
    return AgentResult(agent=agent)


@transaction.atomic
def desactiver_agent(
    *,
    agent_id: int,
    current_user: CustomUser,
) -> 'AgentResult':
    """Désactive un agent (actif=False)."""
    agent = Agent.objects.select_for_update().get(id=agent_id)
    if not agent.actif:
        raise AgentInactifError(f"L'agent {agent.nom} est déjà désactivé.")
    agent.actif = False
    agent.save(update_fields=['actif', 'date_modification'])
    return AgentResult(agent=agent)


@transaction.atomic
def creer_paie(
    *,
    data: 'PaieCreateInput',
    current_user: CustomUser,
) -> PaieResult:
    """Crée un bulletin de paie (wrapper simplifié)."""
    return calculer_bulletin(
        agent_id=data.agent_id,
        mois=data.mois,
        current_user=current_user,
        jp=data.jp,
        absence=data.absence,
    )


@transaction.atomic
def valider_paie(
    *,
    paie_id: int,
    current_user: CustomUser,
) -> 'PaieValidationResult':
    """Valide un bulletin et crée le mouvement caisse."""
    from caisse.models import CaisseCourante, RubriqueCaisse, MouvementCaisseAgent, MouvementCaisse
    
    paie = Paie.objects.select_for_update().get(id=paie_id)
    
    if paie.valide:
        raise PaieDejaValideeError("Le bulletin est déjà validé.")
    
    # Valider le bulletin
    paie.valide = True
    paie.modifie_par = current_user
    paie.save(update_fields=['valide', 'modifie_par', 'date_modification'])
    
    # Créer le mouvement caisse (paiement salaire)
    mouvement_caisse_cree = False
    mouvement_caisse_agent_cree = False
    warning = None
    
    try:
        caisse_courante = CaisseCourante.objects.filter(est_ouverte=True).first()
        if not caisse_courante:
            raise CaissePrincipaleFermeeError("Aucune caisse ouverte.")
        
        rubrique_salaire = RubriqueCaisse.objects.filter(
            nom__iexact='solde sur salaire'
        ).first()
        
        if rubrique_salaire:
            from caisse.models import MouvementCaisseAgent
            
            mois_normalise = paie.mois.replace(day=1)
            mouvement_existant = MouvementCaisse.objects.filter(
                type_mouvement='SORTIE',
                rubrique=rubrique_salaire,
                date_mouvement__month=mois_normalise.month,
                date_mouvement__year=mois_normalise.year,
            ).first()
            
            mouvement_agent_existant = MouvementCaisseAgent.objects.filter(
                agent=paie.agent,
                mouvement_caisse=mouvement_existant,
            ).first() if mouvement_existant else None
            
            if mouvement_agent_existant:
                warning = f"Mouvement caisse salaire déjà existant pour {paie.agent.nom} en {mois_normalise.strftime('%m/%Y')}"
            else:
                mouvement = MouvementCaisse.objects.create(
                    caisse=caisse_courante,
                    type_mouvement='SORTIE',
                    rubrique=rubrique_salaire,
                    montant=paie.net_a_payer,
                    taux_mouvement=paie.taux_creation or get_taux_usd_cdf(),
                    montant_usd=paie.valeur_usd,
                    motif=f"Paiement salaire {paie.agent.nom} {paie.mois.strftime('%m/%Y')}",
                    effectue_par=current_user,
                )
                mouvement_caisse_cree = True
                
                MouvementCaisseAgent.objects.create(
                    mouvement_caisse=mouvement,
                    agent=paie.agent,
                )
                mouvement_caisse_agent_cree = True
    except CaissePrincipaleFermeeError:
        raise
    except Exception:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur création mouvement caisse paie {paie.id}", exc_info=True)
    
    return PaieValidationResult(
        paie=paie,
        warning=warning,
        mouvement_caisse_cree=mouvement_caisse_cree,
        mouvement_caisse_agent_cree=mouvement_caisse_agent_cree,
    )


@transaction.atomic
def supprimer_paie(
    *,
    paie_id: int,
    current_user: CustomUser,
) -> None:
    """Supprime un bulletin (seulement si non validé)."""
    return supprimer_bulletin(paie_id=paie_id, current_user=current_user)


# ── Dataclasses supplémentaires ───────────────────────────────────────────────

class AgentResult:
    def __init__(self, agent: Agent):
        self.agent = agent


class PaieValidationResult:
    def __init__(self, paie: Paie, warning: Optional[str] = None,
                 mouvement_caisse_cree: Optional[bool] = False,
                 mouvement_caisse_agent_cree: Optional[bool] = False):
        self.paie = paie
        self.warning = warning
        self.mouvement_caisse_cree = mouvement_caisse_cree
        self.mouvement_caisse_agent_cree = mouvement_caisse_agent_cree


# ── Selectors (lecture) ───────────────────────────────────────────────────────

def get_bulletin_agent(agent_id: int, mois: date) -> Optional[Paie]:
    """Récupère un bulletin d'agent pour un mois donné."""
    mois_normalise = mois.replace(day=1)
    return Paie.objects.filter(
        agent_id=agent_id,
        mois=mois_normalise
    ).select_related('agent', 'cree_par').first()


def get_bulletins_agent(agent_id: int) -> List[Paie]:
    """Récupère tous les bulletins d'un agent."""
    return list(Paie.objects.filter(agent_id=agent_id).order_by('-mois'))


def get_bulletins_mois(mois: date) -> List[Paie]:
    """Récupère tous les bulletins d'un mois."""
    mois_normalise = mois.replace(day=1)
    return list(Paie.objects.filter(mois=mois_normalise).select_related('agent'))


def get_statistiques_paie(mois: Optional[date] = None) -> Dict:
    """
    Retourne les statistiques de paie pour un mois donné.
    Si mois=None, utilise le mois courant.
    """
    if mois is None:
        mois = timezone.now().date().replace(day=1)
    
    bulletins = get_bulletins_mois(mois)
    
    total_salaire_brut = sum(b.salaire_brut for b in bulletins)
    total_primes = sum(b.total_primes for b in bulletins)
    total_retenues = sum(b.total_retenues for b in bulletins)
    total_net = sum(b.net_a_payer for b in bulletins)
    
    return {
        'mois': mois,
        'nb_bulletins': len(bulletins),
        'total_salaire_brut': total_salaire_brut,
        'total_primes': total_primes,
        'total_retenues': total_retenues,
        'total_net_a_payer': total_net,
    }