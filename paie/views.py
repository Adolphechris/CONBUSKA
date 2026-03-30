"""
paie/views.py

Vues du module paie.
Une vue appelle un service ou un selector — aucune logique métier.
Toutes les CBV héritent de RoleRequiredMixin (LoginRequired implicite).
"""

import datetime
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django_filters.views import FilterView

from caisse.models import MouvementCaisse
from paie.exceptions import (
    AgentInactifError,
    CaissePrincipaleFermeeError,
    PaieDejaExistanteError,
    PaieDejaValideeError,
)
from utils.pdf_generator import DocumentGenerator
from paie.filters import AgentFilter
from paie.forms import AgentForm, PaieCreateForm
from paie.inputs import AgentCreateInput, AgentUpdateInput, PaieCreateInput
from paie.models import Agent, Paie
from paie.selectors import get_agent, get_paie, liste_agents, liste_paies
from paie.services import (
    creer_agent,
    creer_paie,
    desactiver_agent,
    modifier_agent,
    supprimer_paie,
    valider_paie,
)
from users.permissions import ROLE_ADMIN, RoleRequiredMixin


# ── Agents ────────────────────────────────────────────────────────────────────

class AgentsView(RoleRequiredMixin, FilterView):
    allowed_roles = [ROLE_ADMIN]
    model = Agent
    context_object_name = 'liste_agents'
    template_name = 'paie/agents.html'
    filterset_class = AgentFilter

    def get_queryset(self):
        return liste_agents()


class AgentDetailsView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        agent = get_object_or_404(Agent, pk=pk)
        paie_list = liste_paies(agent_id=pk)
        mouvements = (
            MouvementCaisse.objects
            .filter(mouvements_caisse_ag__agent_id=pk)
            .select_related('effectue_par', 'rubrique')
            .order_by('-date_mouvement')
        )
        total_paiements = (
            mouvements.aggregate(total=Sum('montant'))['total'] or Decimal('0')
        )
        return render(request, 'paie/agent_details.html', {
            'agent': agent,
            'paie_list': paie_list,
            'paiements': mouvements,
            'total_paiements': total_paiements,
        })


class AgentCreateView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request):
        return render(request, 'paie/agent_create_form.html', {'form': AgentForm()})

    def post(self, request):
        form = AgentForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, 'paie/agent_create_form.html', {'form': form})

        cd = form.cleaned_data
        result = creer_agent(
            data=AgentCreateInput(
                nom=cd['nom'],
                date_naissance=cd['date_naissance'],
                date_engagement=cd['date_engagement'],
                adresse=cd['adresse'],
                telephone=cd['telephone'],
                ville=cd['ville'],
                salaire=cd['salaire'],
                poste=cd.get('poste') or '',
                departement=cd.get('departement') or '',
                type_contrat=cd.get('type_contrat') or '',
                email=cd.get('email') or None,
            ),
            current_user=request.user,
        )
        if cd.get('photo'):
            result.agent.photo = cd['photo']
            result.agent.save(update_fields=['photo'])

        messages.success(
            request,
            f"Agent {result.agent.nom} créé (matricule {result.agent.matricule}).",
        )
        return redirect('agent_details', pk=result.agent.pk)


class AgentUpdateView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        agent = get_object_or_404(Agent, pk=pk)
        form = AgentForm(initial={
            'nom':            agent.nom,
            'date_naissance': agent.date_naissance,
            'date_engagement': agent.date_engagement,
            'email':          agent.email,
            'telephone':      agent.telephone,
            'adresse':        agent.adresse,
            'ville':          agent.ville,
            'salaire':        agent.salaire,
            'poste':          agent.poste,
            'departement':    agent.departement,
            'type_contrat':   agent.type_contrat,
        })
        return render(request, 'paie/agent_create_form.html', {'form': form, 'agent': agent})

    def post(self, request, pk):
        agent = get_object_or_404(Agent, pk=pk)
        form = AgentForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, 'paie/agent_create_form.html', {'form': form, 'agent': agent})

        cd = form.cleaned_data
        result = modifier_agent(
            data=AgentUpdateInput(
                agent_id=pk,
                nom=cd['nom'],
                date_naissance=cd['date_naissance'],
                date_engagement=cd['date_engagement'],
                adresse=cd['adresse'],
                telephone=cd['telephone'],
                ville=cd['ville'],
                salaire=cd['salaire'],
                poste=cd.get('poste') or '',
                departement=cd.get('departement') or '',
                type_contrat=cd.get('type_contrat') or '',
                email=cd.get('email') or None,
            ),
            current_user=request.user,
        )
        if cd.get('photo'):
            result.agent.photo = cd['photo']
            result.agent.save(update_fields=['photo'])

        messages.success(request, f"Agent {result.agent.nom} modifié.")
        return redirect('agent_details', pk=pk)


class AgentDeleteView(RoleRequiredMixin, View):
    """Désactivation logique d'un agent (actif=False)."""
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        agent = get_object_or_404(Agent, pk=pk)
        return render(request, 'paie/agent_confirm_delete.html', {
            'agent':        agent,
            'title':        'Désactiver un agent',
            'message':      f"Voulez-vous désactiver l'agent « {agent} » ? Il ne pourra plus faire l'objet d'une paie.",
            'submit_icon':  'fa fa-ban',
            'submit_label': 'Désactiver',
        })

    def post(self, request, pk):
        try:
            result = desactiver_agent(agent_id=pk, current_user=request.user)
            messages.success(request, f"Agent {result.agent.nom} désactivé.")
        except AgentInactifError as e:
            messages.warning(request, str(e))
        return redirect('agents')


# ── Paie ──────────────────────────────────────────────────────────────────────

class PaieAgentCreateView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def _get_agent(self, pk):
        return get_object_or_404(Agent, pk=pk)

    def get(self, request, pk):
        initial_mois = datetime.date.today().strftime('%Y-%m')
        return render(request, 'paie/paie_create_form.html', {
            'form':  PaieCreateForm(initial={'mois': initial_mois}),
            'agent': self._get_agent(pk),
        })

    def post(self, request, pk):
        agent = self._get_agent(pk)
        form = PaieCreateForm(request.POST)
        if not form.is_valid():
            return render(request, 'paie/paie_create_form.html', {'form': form, 'agent': agent})

        cd = form.cleaned_data
        absence = cd.get('absence') or 0
        jap = 26
        jp = jap - absence

        try:
            result = creer_paie(
                data=PaieCreateInput(
                    agent_id=pk,
                    mois=cd['mois'],
                    jap=jap,
                    jp=jp,
                    absence=absence,
                ),
                current_user=request.user,
            )
        except PaieDejaExistanteError as e:
            paie_existante = Paie.objects.filter(
                agent_id=pk,
                mois=cd['mois'].replace(day=1),
            ).first()
            messages.warning(request, str(e))
            if paie_existante:
                return redirect('paie_agent_details', pk=paie_existante.pk, agent_pk=pk)
            form.add_error(None, str(e))
            return render(request, 'paie/paie_create_form.html', {'form': form, 'agent': agent})
        except AgentInactifError as e:
            form.add_error(None, str(e))
            return render(request, 'paie/paie_create_form.html', {'form': form, 'agent': agent})

        return redirect('paie_agent_details', pk=result.paie.pk, agent_pk=pk)


class PaieAgentDetailsView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk, agent_pk):
        paie = get_object_or_404(Paie, pk=pk, agent_id=agent_pk)
        agent = get_object_or_404(Agent, pk=agent_pk)
        lignes = list(paie.lignes.all())
        details_paie_agent = [
            {'libelle': l.libelle, 'montant': l.montant}
            for l in lignes
        ]
        lignes_gain    = [l for l in lignes if l.type_ligne == 'GAIN']
        lignes_retenue = [l for l in lignes if l.type_ligne == 'RETENUE']
        return render(request, 'paie/paie_details.html', {
            'paie':               paie,
            'agent':              agent,
            'lignes':             lignes,
            'lignes_gain':        lignes_gain,
            'lignes_retenue':     lignes_retenue,
            'details_paie_agent': details_paie_agent,
            'total_remuneration': paie.net_a_payer,
        })


class PaieAgentDeleteView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def post(self, request, pk, agent_pk):
        try:
            supprimer_paie(paie_id=pk, current_user=request.user)
            messages.success(request, "Paie supprimée.")
        except PaieDejaValideeError as e:
            messages.error(request, str(e))
        except Paie.DoesNotExist:
            messages.error(request, "Paie introuvable.")
        return redirect('agent_details', pk=agent_pk)


class PaieValiderView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def post(self, request, pk, agent_pk):
        try:
            result = valider_paie(paie_id=pk, current_user=request.user)
            if result.warning:
                messages.warning(request, result.warning)
            messages.success(request, "Paie validée. Mouvement caisse enregistré.")
        except PaieDejaValideeError as e:
            messages.error(request, str(e))
        except CaissePrincipaleFermeeError as e:
            messages.error(request, str(e))
        return redirect('paie_agent_details', pk=pk, agent_pk=agent_pk)


class PaiePdfView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk, agent_pk):
        paie = get_object_or_404(Paie, pk=pk, agent_id=agent_pk)
        lignes = paie.lignes.all().order_by('ordre', 'id')
        gen = DocumentGenerator(
            filename=f'bulletin_paie_{paie.agent.matricule}_{paie.mois:%Y_%m}.pdf',
            title=f'Bulletin de paie — {paie.agent.nom}',
        )
        return gen.generate_bulletin_paie(paie=paie, lignes=lignes)


class ListePaiesView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request):
        mois_param = request.GET.get('mois')  # format YYYY-MM
        mois = None
        if mois_param:
            try:
                mois = datetime.date.fromisoformat(f"{mois_param}-01")
            except ValueError:
                pass
        if mois is None:
            mois = datetime.date.today().replace(day=1)

        paies = liste_paies(mois=mois)
        nb_validees   = paies.filter(valide=True).count()
        nb_brouillons = paies.filter(valide=False).count()
        masse_salariale = (
            paies.filter(valide=True)
            .aggregate(total=Sum('net_a_payer'))['total']
            or Decimal('0')
        )
        return render(request, 'paie/paies.html', {
            'liste_paies':    paies,
            'mois':           mois,
            'mois_str':       mois.strftime('%Y-%m'),
            'nb_total':       nb_validees + nb_brouillons,
            'nb_validees':    nb_validees,
            'nb_brouillons':  nb_brouillons,
            'masse_salariale': masse_salariale,
        })
