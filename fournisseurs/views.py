from users.permissions import RoleRequiredMixin, ROLE_ADMIN
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django_filters.views import FilterView
from .models import Fournisseur
from .forms import FournisseurCreateForm
from .filters import FournisseurFilter


class FournisseursView(RoleRequiredMixin, FilterView):
    allowed_roles = [ROLE_ADMIN]
    model = Fournisseur
    context_object_name = 'liste_fournisseurs'
    template_name = 'fournisseurs/fournisseurs.html'
    filterset_class = FournisseurFilter

    def get_queryset(self):
        return Fournisseur.objects.filter(actif=True).order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filtered_qs = self.object_list

        context['f_systemes'] = filtered_qs.filter(is_system=True)
        context['f_ordinaires'] = filtered_qs.filter(is_system=False)

        # Calcul du solde total basé uniquement sur les résultats filtrés
        context['total_solde'] = sum(f.solde() for f in filtered_qs)

        return context


class FournisseurDetailsView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
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


class FournisseurCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = Fournisseur
    template_name = 'fournisseurs/fournisseur_create_form.html'
    form_class = FournisseurCreateForm


class FournisseurUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Fournisseur
    template_name = 'fournisseurs/fournisseur_create_form.html'
    form_class = FournisseurCreateForm


class FournisseurDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [ROLE_ADMIN]
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
