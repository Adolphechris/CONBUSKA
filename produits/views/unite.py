from users.permissions import RoleRequiredMixin, ROLE_ADMIN
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from produits.models import Unite
from produits.forms import UniteCreateForm


class UniteView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = Unite
    context_object_name = 'liste_unites'
    template_name = 'produits/unite/unites.html'


class UniteDetailsView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = Unite
    context_object_name = 'unite'
    template_name = 'produits/unite/unite_details.html'


class UniteCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = Unite
    template_name = 'produits/unite/unite_create_form.html'
    form_class = UniteCreateForm


class UniteUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Unite
    template_name = 'produits/unite/unite_create_form.html'
    form_class = UniteCreateForm


class UniteDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [ROLE_ADMIN]
    model = Unite
    template_name = 'produits/unite/unite_confirm_delete.html'
    success_url = reverse_lazy('unites')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer une unite'
        context['message'] = "Voulez-vous supprimer l'unite {} ?".format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context
