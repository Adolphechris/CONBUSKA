from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django_filters.views import FilterView
from .models import Fournisseur
from .forms import FournisseurCreateForm
from .filters import FournisseurFilter


class FournisseursView(LoginRequiredMixin, FilterView):
    model = Fournisseur
    context_object_name = 'liste_fournisseurs'
    template_name = 'fournisseurs/fournisseurs.html'
    filterset_class = FournisseurFilter

    def get_queryset(self):
        return Fournisseur.objects.filter(actif=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fournisseurs = Fournisseur.objects.filter(actif=True).order_by('nom')
        context['f_systemes'] = fournisseurs.filter(is_system=True)
        context['f_ordinaires'] = fournisseurs.filter(is_system=False)
        context['total_solde'] = sum(fournisseur.solde() for fournisseur in fournisseurs)
        return context


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
