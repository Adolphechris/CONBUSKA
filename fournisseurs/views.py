from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Fournisseur
from .forms import FournisseurCreateForm


class FournisseursView(LoginRequiredMixin, ListView):
    model = Fournisseur
    context_object_name = 'liste_fournisseurs'
    template_name = 'fournisseurs/fournisseurs.html'


class FournisseurDetailsView(LoginRequiredMixin, DetailView):
    model = Fournisseur
    context_object_name = 'fournisseur'
    template_name = 'fournisseurs/fournisseur_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fournisseur = self.object

        context['mouvements'] = fournisseur.mouvements()
        context['paiements'] = fournisseur.paiements()
        context['total_mouvements'] = fournisseur.total_mouvements()
        context['total_paiements'] = fournisseur.total_paiements()
        context['solde_fournisseur'] = fournisseur.solde()
        return context


class FournisseurCreateView(LoginRequiredMixin, CreateView):
    model = Fournisseur
    template_name = 'fournisseurs/fournisseur_create_form.html'
    form_class = FournisseurCreateForm


class FournisseurUpdateView(LoginRequiredMixin, UpdateView):
    model = Fournisseur
    template_name = 'fournisseurs/fournisseur_create_form.html'
    form_class = FournisseurCreateForm


class FournisseurDeleteView(LoginRequiredMixin, DeleteView):
    model = Fournisseur
    template_name = 'fournisseurs/fournisseur_confirm_delete.html'
    success_url = reverse_lazy('fournisseurs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer un fournisseur'
        context['message'] = 'Voulez-vous supprimer le fournisseur {} ?'.format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context
