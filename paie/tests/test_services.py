"""
paie/tests/test_services.py

Tests des services du module paie.
Couvre : cas nominal, cas d'erreur métier, effets sur la DB, intégration caisse.
"""

import datetime
from decimal import Decimal

import pytest

from caisse.models import MouvementCaisse, MouvementCaisseAgent
from paie.exceptions import (
    AgentInactifError,
    CaissePrincipaleFermeeError,
    PaieDejaExistanteError,
    PaieDejaValideeError,
)
from paie.inputs import AgentCreateInput, AgentUpdateInput, PaieCreateInput
from paie.models import Agent, LignePaie, Paie, TypeLigne
from paie.services import (
    creer_agent,
    creer_paie,
    desactiver_agent,
    modifier_agent,
    supprimer_paie,
    valider_paie,
)

from .factories import (
    AgentFactory,
    CaisseCouranteFactory,
    CaisseFactory,
    CustomUserFactory,
    LignePaieFactory,
    MouvementCaisseAgentFactory,
    MouvementCaisseFactory,
    PaieFactory,
    RubriqueCaisseFactory,
)

MOIS_TEST = datetime.date(2026, 3, 1)


# ── creer_agent ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreerAgent:
    def _input(self, **kwargs):
        defaults = dict(
            nom="Dupont Jean",
            date_naissance=datetime.date(1990, 5, 15),
            date_engagement=datetime.date(2020, 1, 1),
            adresse="12 rue test",
            telephone="0812345678",
            ville="Kinshasa",
            salaire=Decimal('2000.00'),
        )
        defaults.update(kwargs)
        return AgentCreateInput(**defaults)

    def test_nominal(self):
        user = CustomUserFactory()
        result = creer_agent(data=self._input(), current_user=user)
        assert result.agent.pk is not None
        assert result.agent.nom == "Dupont Jean"
        assert result.agent.actif is True

    def test_matricule_auto_incremente(self):
        user = CustomUserFactory()
        AgentFactory(matricule=5)
        result = creer_agent(data=self._input(), current_user=user)
        assert result.agent.matricule == 6

    def test_premier_matricule_est_1_si_aucun_agent(self):
        user = CustomUserFactory()
        result = creer_agent(data=self._input(), current_user=user)
        assert result.agent.matricule == 1

    def test_persiste_en_db(self):
        user = CustomUserFactory()
        result = creer_agent(data=self._input(), current_user=user)
        assert Agent.objects.filter(pk=result.agent.pk).exists()


# ── modifier_agent ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestModifierAgent:
    def _input(self, agent, **kwargs):
        defaults = dict(
            agent_id=agent.pk,
            nom=agent.nom,
            date_naissance=agent.date_naissance,
            date_engagement=agent.date_engagement,
            adresse=agent.adresse,
            telephone=agent.telephone,
            ville=agent.ville,
            salaire=agent.salaire,
        )
        defaults.update(kwargs)
        return AgentUpdateInput(**defaults)

    def test_nominal(self):
        user = CustomUserFactory()
        agent = AgentFactory(salaire=Decimal('1500.00'))
        data = self._input(agent, salaire=Decimal('2000.00'), poste="Manager")
        result = modifier_agent(data=data, current_user=user)
        assert result.agent.salaire == Decimal('2000.00')
        assert result.agent.poste == "Manager"

    def test_persiste_en_db(self):
        user = CustomUserFactory()
        agent = AgentFactory()
        modifier_agent(
            data=self._input(agent, ville="Lubumbashi"),
            current_user=user,
        )
        agent.refresh_from_db()
        assert agent.ville == "Lubumbashi"

    def test_leve_does_not_exist_si_introuvable(self):
        user = CustomUserFactory()
        with pytest.raises(Agent.DoesNotExist):
            modifier_agent(
                data=AgentUpdateInput(
                    agent_id=99999,
                    nom="X",
                    date_naissance=datetime.date(1990, 1, 1),
                    date_engagement=datetime.date(2020, 1, 1),
                    adresse="X",
                    telephone="X",
                    ville="X",
                    salaire=Decimal('1000.00'),
                ),
                current_user=user,
            )


# ── desactiver_agent ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDesactiverAgent:
    def test_nominal(self):
        user = CustomUserFactory()
        agent = AgentFactory(actif=True)
        result = desactiver_agent(agent_id=agent.pk, current_user=user)
        assert result.agent.actif is False

    def test_persiste_en_db(self):
        user = CustomUserFactory()
        agent = AgentFactory(actif=True)
        desactiver_agent(agent_id=agent.pk, current_user=user)
        agent.refresh_from_db()
        assert agent.actif is False

    def test_leve_erreur_si_deja_inactif(self):
        user = CustomUserFactory()
        agent = AgentFactory(actif=False)
        with pytest.raises(AgentInactifError):
            desactiver_agent(agent_id=agent.pk, current_user=user)


# ── creer_paie ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreerPaie:
    def test_nominal_sans_primes(self):
        user = CustomUserFactory()
        agent = AgentFactory(salaire=Decimal('2600.00'), actif=True)
        data = PaieCreateInput(agent_id=agent.pk, mois=MOIS_TEST, jap=26, jp=26, absence=0)
        result = creer_paie(data=data, current_user=user)

        paie = result.paie
        assert paie.pk is not None
        assert paie.salaire_base == Decimal('2600.00')
        assert paie.salaire_brut == Decimal('2600.00')
        assert paie.total_primes == Decimal('0.00')
        assert paie.total_retenues == Decimal('0.00')
        assert paie.net_a_payer == Decimal('2600.00')
        assert paie.valide is False

    def test_normalise_mois_au_premier(self):
        user = CustomUserFactory()
        agent = AgentFactory()
        data = PaieCreateInput(agent_id=agent.pk, mois=datetime.date(2026, 3, 15))
        result = creer_paie(data=data, current_user=user)
        assert result.paie.mois == MOIS_TEST

    def test_prorata_jours(self):
        user = CustomUserFactory()
        agent = AgentFactory(salaire=Decimal('2600.00'))
        # 20 jours payés sur 26
        data = PaieCreateInput(agent_id=agent.pk, mois=MOIS_TEST, jap=26, jp=20, absence=6)
        result = creer_paie(data=data, current_user=user)
        # 2600 * 20 / 26 = 2000.00
        assert result.paie.salaire_brut == Decimal('2000.00')

    def test_cree_lignes_paie(self):
        user = CustomUserFactory()
        agent = AgentFactory(salaire=Decimal('1500.00'))
        data = PaieCreateInput(agent_id=agent.pk, mois=MOIS_TEST)
        result = creer_paie(data=data, current_user=user)
        lignes = list(result.paie.lignes.all())
        assert len(lignes) == 1  # seulement salaire_base
        assert lignes[0].type_ligne == TypeLigne.GAIN

    def test_avec_primes_et_avance_depuis_caisse(self):
        user = CustomUserFactory()
        agent = AgentFactory(salaire=Decimal('2000.00'))
        caisse = CaisseCouranteFactory()
        mois_aujourd_hui = datetime.date.today().replace(day=1)

        rubrique_transport = RubriqueCaisseFactory(nom="Transport")
        rubrique_avance = RubriqueCaisseFactory(nom="Avance sur salaire")

        mv_transport = MouvementCaisseFactory(
            caisse=caisse, rubrique=rubrique_transport, montant=Decimal('200.00'),
            type_mouvement='ENTREE',
        )
        MouvementCaisseAgentFactory(mouvement_caisse=mv_transport, agent=agent)

        mv_avance = MouvementCaisseFactory(
            caisse=caisse, rubrique=rubrique_avance, montant=Decimal('500.00'),
            type_mouvement='SORTIE',
        )
        MouvementCaisseAgentFactory(mouvement_caisse=mv_avance, agent=agent)

        data = PaieCreateInput(agent_id=agent.pk, mois=mois_aujourd_hui)
        result = creer_paie(data=data, current_user=user)

        paie = result.paie
        assert paie.total_primes == Decimal('200.00')
        assert paie.total_retenues == Decimal('500.00')
        assert paie.net_a_payer == Decimal('1700.00')  # 2000 + 200 - 500

        noms_lignes = list(paie.lignes.values_list('libelle', flat=True))
        assert "Transport" in noms_lignes
        assert "Avance sur salaire" in noms_lignes

    def test_leve_erreur_si_paie_deja_existante(self):
        user = CustomUserFactory()
        agent = AgentFactory()
        PaieFactory(agent=agent, mois=MOIS_TEST)
        data = PaieCreateInput(agent_id=agent.pk, mois=MOIS_TEST)
        with pytest.raises(PaieDejaExistanteError):
            creer_paie(data=data, current_user=user)

    def test_leve_erreur_si_agent_inactif(self):
        user = CustomUserFactory()
        agent = AgentFactory(actif=False)
        data = PaieCreateInput(agent_id=agent.pk, mois=MOIS_TEST)
        with pytest.raises(AgentInactifError):
            creer_paie(data=data, current_user=user)


# ── supprimer_paie ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSupprimerPaie:
    def test_nominal(self):
        user = CustomUserFactory()
        paie = PaieFactory(valide=False)
        pk = paie.pk
        supprimer_paie(paie_id=pk, current_user=user)
        assert not Paie.objects.filter(pk=pk).exists()

    def test_supprime_les_lignes_en_cascade(self):
        user = CustomUserFactory()
        paie = PaieFactory(valide=False)
        ligne = LignePaieFactory(paie=paie)
        supprimer_paie(paie_id=paie.pk, current_user=user)
        assert not LignePaie.objects.filter(pk=ligne.pk).exists()

    def test_leve_erreur_si_deja_validee(self):
        user = CustomUserFactory()
        paie = PaieFactory(valide=True)
        with pytest.raises(PaieDejaValideeError):
            supprimer_paie(paie_id=paie.pk, current_user=user)

    def test_leve_does_not_exist_si_introuvable(self):
        user = CustomUserFactory()
        with pytest.raises(Paie.DoesNotExist):
            supprimer_paie(paie_id=99999, current_user=user)


# ── valider_paie ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestValiderPaie:
    def _setup_caisse(self):
        """Crée une caisse principale ouverte + rubrique Solde sur salaire."""
        caisse_obj = CaisseFactory(is_principal=True)
        caisse_courante = CaisseCouranteFactory(caisse=caisse_obj)
        rubrique = RubriqueCaisseFactory(nom="Solde sur salaire")
        return caisse_courante, rubrique

    def test_nominal_valide_la_paie(self):
        user = CustomUserFactory()
        self._setup_caisse()
        paie = PaieFactory(valide=False, net_a_payer=Decimal('2000.00'))
        result = valider_paie(paie_id=paie.pk, current_user=user)
        assert result.paie.valide is True
        assert result.mouvement_caisse_cree is True
        assert result.warning is None

    def test_cree_mouvement_caisse_sortie(self):
        user = CustomUserFactory()
        caisse_courante, rubrique = self._setup_caisse()
        paie = PaieFactory(valide=False, net_a_payer=Decimal('1800.00'))
        valider_paie(paie_id=paie.pk, current_user=user)

        mouvement = MouvementCaisse.objects.get(
            caisse=caisse_courante,
            rubrique=rubrique,
            type_mouvement='SORTIE',
        )
        assert mouvement.montant == Decimal('1800.00')

    def test_cree_mouvement_caisse_agent(self):
        user = CustomUserFactory()
        self._setup_caisse()
        paie = PaieFactory(valide=False)
        valider_paie(paie_id=paie.pk, current_user=user)
        assert MouvementCaisseAgent.objects.filter(agent=paie.agent).exists()

    def test_persiste_valide_en_db(self):
        user = CustomUserFactory()
        self._setup_caisse()
        paie = PaieFactory(valide=False)
        valider_paie(paie_id=paie.pk, current_user=user)
        paie.refresh_from_db()
        assert paie.valide is True

    def test_idempotent_si_mouvement_deja_existant(self):
        user = CustomUserFactory()
        caisse_courante, rubrique = self._setup_caisse()
        paie = PaieFactory(valide=False, mois=datetime.date.today().replace(day=1))

        # Simule un mouvement caisse déjà créé manuellement pour cet agent ce mois
        mv = MouvementCaisseFactory(caisse=caisse_courante, rubrique=rubrique)
        MouvementCaisseAgentFactory(mouvement_caisse=mv, agent=paie.agent)

        nb_mouvements_avant = MouvementCaisse.objects.count()
        result = valider_paie(paie_id=paie.pk, current_user=user)

        assert result.mouvement_caisse_cree is False
        assert result.warning is not None
        assert MouvementCaisse.objects.count() == nb_mouvements_avant  # pas de doublon
        assert result.paie.valide is True

    def test_leve_erreur_si_deja_validee(self):
        user = CustomUserFactory()
        self._setup_caisse()
        paie = PaieFactory(valide=True)
        with pytest.raises(PaieDejaValideeError):
            valider_paie(paie_id=paie.pk, current_user=user)

    def test_leve_erreur_si_caisse_principale_fermee(self):
        user = CustomUserFactory()
        # Aucune caisse principale ouverte
        paie = PaieFactory(valide=False)
        with pytest.raises(CaissePrincipaleFermeeError):
            valider_paie(paie_id=paie.pk, current_user=user)
