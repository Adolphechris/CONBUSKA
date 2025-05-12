from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from .models import Fournisseur, PaiementFournisseur
from approvisionnements.models import DetailsApprovisionnement
from .forms import FournisseurCreateForm, PaiementFournisseurCreateForm


class FournisseursView(LoginRequiredMixin, ListView):
    model = Fournisseur
    context_object_name = 'liste_fournisseurs'
    template_name = 'fournisseurs/fournisseurs.html'
    """
    def get_mouvements(self):
        get_details_appro = DetailsApprovisionnement.objects.filter(fournisseur=self.get_object())
        return get_details_appro

    def get_paiements(self):
        paiements = PaiementFournisseur.objects.filter(fournisseur=self.get_object())
        return paiements

    def total_mouvements(self):
        total = sum(i.prix_total for i in self.get_mouvements())
        return total

    def total_paiements(self):
        total = sum(i.montant for i in self.get_paiements())
        return total

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['solde_fournisseur'] = self.total_mouvements() - self.total_paiements()
        return context
    """


class FournisseurDetailsView(LoginRequiredMixin, DetailView):
    model = Fournisseur
    context_object_name = 'fournisseur'
    template_name = 'fournisseurs/fournisseur_details.html'

    def get_mouvements(self):
        get_details_appro = DetailsApprovisionnement.objects.filter(fournisseur=self.get_object())
        return get_details_appro

    def get_paiements(self):
        paiements = PaiementFournisseur.objects.filter(fournisseur=self.get_object())
        return paiements

    def total_mouvements(self):
        total = sum(i.prix_total for i in self.get_mouvements())
        return total

    def total_paiements(self):
        total = sum(i.montant for i in self.get_paiements())
        return total

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mouvements'] = self.get_mouvements()
        context['paiements'] = self.get_paiements()
        context['total_mouvements'] = self.total_mouvements()
        context['total_paiements'] = self.total_paiements()
        context['solde_fournisseur'] = self.total_mouvements() - self.total_paiements()
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


class PaiementFournisseurCreateView(LoginRequiredMixin, CreateView):
    model = PaiementFournisseur
    template_name = 'fournisseurs/paiement_fournisseur_create_form.html'
    form_class = PaiementFournisseurCreateForm

    def get_fournisseur(self):
        return get_object_or_404(Fournisseur, pk=self.kwargs['pk'])

    def form_valid(self, form, *args, **kwargs):
        paiement = form.save(commit=False)
        paiement.fournisseur = self.get_fournisseur()
        paiement.cree_par = self.request.user
        paiement.save()
        return redirect('fournisseur_details', pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fournisseur'] = self.get_fournisseur()
        return context
