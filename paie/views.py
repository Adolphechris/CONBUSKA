from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, RedirectView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Agent, Paie, DetailsPaie
from .forms import AgentCreateForm, PaiePeriodeForm, PaieCreateForm
import datetime


class AgentsView(LoginRequiredMixin, ListView):
    model = Agent
    context_object_name = 'liste_agents'
    template_name = 'paie/agents.html'


class AgentDetailsView(LoginRequiredMixin, DetailView):
    model = Agent
    context_object_name = 'agent'
    template_name = 'paie/agent_details.html'


class AgentCreateView(LoginRequiredMixin, CreateView):
    model = Agent
    template_name = 'paie/agent_create_form.html'
    form_class = AgentCreateForm


class AgentUpdateView(LoginRequiredMixin, UpdateView):
    model = Agent
    template_name = 'paie/agent_create_form.html'
    form_class = AgentCreateForm


class AgentDeleteView(LoginRequiredMixin, DeleteView):
    model = Agent
    template_name = 'paie/agent_confirm_delete.html'
    success_url = reverse_lazy('agents')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer un agent'
        context['message'] = "Voulez-vous supprimer l'agent {} ?".format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context


class ListePaiesView(LoginRequiredMixin, ListView):
    model = Paie
    context_object_name = 'liste_paies'
    template_name = 'paie/paies.html'


class PaieCreateView(LoginRequiredMixin, FormView):
    """
        Cette vue permet de selectionner une periode de paie basée sur l'année et le mois. Ex: 2025-07.
        Ensuite elle crée l'instance de Paie et génère les DetailsPaie pour tous les agents.
    """
    model = Paie
    template_name = 'paie/paie_create_form.html'
    form_class = PaiePeriodeForm

    def form_valid(self, form):
        mois = form.cleaned_data['mois']

        # Empêcher les périodes futures
        if mois > datetime.date.today():
            messages.error(self.request, "Impossible de générer la paie dans le futur.")
            return self.form_invalid(form)

        paie_instance = Paie.objects.create(
            mois=mois.replace(day=1),
            cree_par=self.request.user
        )

        # Génération des DetailsPaie pour chaque agent
        agents = Agent.objects.all()
        for agent in agents:
            DetailsPaie.objects.create(
                paie=paie_instance,
                agent=agent,
                salaire=agent.salaire,
                montant_percu=agent.salaire,
            )

        return redirect('paie_details', pk=paie_instance.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class PaieDetailsView(LoginRequiredMixin, DetailView):
    model = Paie
    context_object_name = 'paie'
    template_name = 'paie/paie_details.html'

    def get_paie(self):
        return get_object_or_404(Paie, pk=self.kwargs['pk'])

    def get_paie_agents(self):
        agents = Agent.objects.all()
        paie = self.get_paie()
        liste_paie = []
        for i in agents:
            details_paie = DetailsPaie.objects.get(agent=i.pk, paie=paie)
            dico = dict()
            dico['agent'] = i
            dico['montant_percu'] = details_paie.montant_percu
            dico['jap'] = details_paie.jap
            dico['jp'] = details_paie.jp
            dico['absence'] = details_paie.absence
            liste_paie.append(dico)

        return liste_paie

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paie_agents'] = self.get_paie_agents()
        return context


class PaieAgentCreateView(LoginRequiredMixin, CreateView):
    model = DetailsPaie
    template_name = 'paie/paie_agent_create_form.html'
    form_class = PaieCreateForm

    def get_paie(self):
        return get_object_or_404(Paie, pk=self.kwargs['pk'])

    def get_agent(self):
        return get_object_or_404(Agent, pk=self.kwargs['agent_pk'])

    def form_valid(self, form):
        paie = self.get_paie()
        agent = self.get_agent()
        detail = form.save(commit=False)
        detail.paie = paie
        detail.agent = agent
        detail.salaire = agent.salaire
        detail.save()

        return redirect('paie_details', pk=paie.pk)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agent'] = self.get_agent()
        context['paie'] = self.get_paie()
        return context