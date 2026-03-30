"""
paie/tests/test_selectors.py

Tests des selectors du module paie.
Couvre : requêtes nominales, cas absents, filtres, cumuls caisse.
"""

import datetime
from decimal import Decimal

import pytest

from paie.models import Agent, Paie
from paie.selectors import (
    cumul_caisse_par_rubrique,
    existe_agent_par_matricule,
    existe_paie,
    get_agent,
    get_paie,
    liste_agents,
    liste_paies,
)

from .factories import (
    AgentFactory,
    CaisseCouranteFactory,
    MouvementCaisseAgentFactory,
    MouvementCaisseFactory,
    PaieFactory,
    RubriqueCaisseFactory,
)


# ── get_agent ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetAgent:
    def test_nominal(self):
        agent = AgentFactory()
        result = get_agent(agent_id=agent.pk)
        assert result.pk == agent.pk

    def test_leve_does_not_exist_si_introuvable(self):
        with pytest.raises(Agent.DoesNotExist):
            get_agent(agent_id=99999)


# ── liste_agents ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestListeAgents:
    def test_retourne_tous_les_agents(self):
        AgentFactory.create_batch(3)
        assert liste_agents().count() == 3

    def test_filtre_actifs(self):
        AgentFactory(actif=True)
        AgentFactory(actif=False)
        assert liste_agents(actif=True).count() == 1
        assert liste_agents(actif=False).count() == 1

    def test_sans_filtre_retourne_tout(self):
        AgentFactory(actif=True)
        AgentFactory(actif=False)
        assert liste_agents().count() == 2


# ── existe_agent_par_matricule ────────────────────────────────────────────────

@pytest.mark.django_db
class TestExisteAgentParMatricule:
    def test_true_si_matricule_existe(self):
        agent = AgentFactory(matricule=42)
        assert existe_agent_par_matricule(matricule=42) is True

    def test_false_si_matricule_absent(self):
        assert existe_agent_par_matricule(matricule=9999) is False

    def test_exclude_id_ignore_agent_concerne(self):
        agent = AgentFactory(matricule=42)
        # Même matricule mais on exclut l'agent — doit retourner False
        assert existe_agent_par_matricule(matricule=42, exclude_id=agent.pk) is False

    def test_exclude_id_detecte_conflit_avec_autre(self):
        a1 = AgentFactory(matricule=42)
        a2 = AgentFactory(matricule=43)
        # On vérifie si matricule 42 est pris par quelqu'un d'autre que a2
        assert existe_agent_par_matricule(matricule=42, exclude_id=a2.pk) is True


# ── get_paie ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetPaie:
    def test_nominal(self):
        paie = PaieFactory()
        result = get_paie(paie_id=paie.pk)
        assert result.pk == paie.pk

    def test_leve_does_not_exist_si_introuvable(self):
        with pytest.raises(Paie.DoesNotExist):
            get_paie(paie_id=99999)


# ── liste_paies ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestListePaies:
    def test_retourne_toutes_les_paies(self):
        PaieFactory.create_batch(3, mois=datetime.date(2026, 1, 1))
        assert liste_paies().count() == 3

    def test_filtre_par_mois(self):
        PaieFactory(mois=datetime.date(2026, 1, 1))
        PaieFactory(mois=datetime.date(2026, 2, 1))
        result = liste_paies(mois=datetime.date(2026, 1, 15))
        assert result.count() == 1
        assert result.first().mois == datetime.date(2026, 1, 1)

    def test_filtre_par_agent(self):
        a1 = AgentFactory()
        a2 = AgentFactory()
        PaieFactory(agent=a1, mois=datetime.date(2026, 1, 1))
        PaieFactory(agent=a2, mois=datetime.date(2026, 1, 1))
        assert liste_paies(agent_id=a1.pk).count() == 1


# ── existe_paie ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestExistePaie:
    def test_true_si_paie_existe(self):
        agent = AgentFactory()
        PaieFactory(agent=agent, mois=datetime.date(2026, 1, 1))
        assert existe_paie(agent_id=agent.pk, mois=datetime.date(2026, 1, 1)) is True

    def test_false_si_paie_absente(self):
        agent = AgentFactory()
        assert existe_paie(agent_id=agent.pk, mois=datetime.date(2026, 1, 1)) is False

    def test_normalise_mois_au_premier(self):
        agent = AgentFactory()
        PaieFactory(agent=agent, mois=datetime.date(2026, 1, 1))
        # Passer le 15 doit trouver la paie du 1er
        assert existe_paie(agent_id=agent.pk, mois=datetime.date(2026, 1, 15)) is True


# ── cumul_caisse_par_rubrique ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestCumulCaisseParRubrique:
    def test_retourne_dict_vide_si_aucun_mouvement(self):
        agent = AgentFactory()
        result = cumul_caisse_par_rubrique(
            agent_id=agent.pk, mois=datetime.date(2026, 3, 1)
        )
        assert result == {}

    def test_cumule_un_seul_mouvement(self):
        agent = AgentFactory()
        caisse = CaisseCouranteFactory()
        rubrique = RubriqueCaisseFactory(nom="Transport")
        mouvement = MouvementCaisseFactory(
            caisse=caisse, rubrique=rubrique, montant=Decimal('200.00')
        )
        MouvementCaisseAgentFactory(mouvement_caisse=mouvement, agent=agent)

        result = cumul_caisse_par_rubrique(
            agent_id=agent.pk, mois=datetime.date.today().replace(day=1)
        )
        assert result.get("Transport") == Decimal('200.00')

    def test_cumule_plusieurs_mouvements_meme_rubrique(self):
        agent = AgentFactory()
        caisse = CaisseCouranteFactory()
        rubrique = RubriqueCaisseFactory(nom="Transport")
        for montant in (Decimal('100.00'), Decimal('150.00')):
            mv = MouvementCaisseFactory(caisse=caisse, rubrique=rubrique, montant=montant)
            MouvementCaisseAgentFactory(mouvement_caisse=mv, agent=agent)

        result = cumul_caisse_par_rubrique(
            agent_id=agent.pk, mois=datetime.date.today().replace(day=1)
        )
        assert result.get("Transport") == Decimal('250.00')

    def test_isole_les_mouvements_par_agent(self):
        a1 = AgentFactory()
        a2 = AgentFactory()
        caisse = CaisseCouranteFactory()
        rubrique = RubriqueCaisseFactory(nom="Transport")
        mv = MouvementCaisseFactory(caisse=caisse, rubrique=rubrique, montant=Decimal('300.00'))
        MouvementCaisseAgentFactory(mouvement_caisse=mv, agent=a1)

        result = cumul_caisse_par_rubrique(
            agent_id=a2.pk, mois=datetime.date.today().replace(day=1)
        )
        assert result == {}
