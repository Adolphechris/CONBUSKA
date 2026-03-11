from users.permissions import RoleRequiredMixin, ROLE_ADMIN
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from produits.models import Categorie
from produits.forms import CategorieCreateForm


class CategorieView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = Categorie
    context_object_name = 'liste_categories'
    template_name = 'produits/categorie/categories.html'


class CategorieDetailsView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = Categorie
    context_object_name = 'categorie'
    template_name = 'produits/categorie/categorie_details.html'


class CategorieCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = Categorie
    template_name = 'produits/categorie/categorie_create_form.html'
    form_class = CategorieCreateForm


class CategorieUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Categorie
    template_name = 'produits/categorie/categorie_create_form.html'
    form_class = CategorieCreateForm


class CategorieDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [ROLE_ADMIN]
    model = Categorie
    template_name = 'produits/categorie/categorie_confirm_delete.html'
    success_url = reverse_lazy('categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer une categorie'
        context['message'] = 'Voulez-vous supprimer la categorie {} ?'.format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context
