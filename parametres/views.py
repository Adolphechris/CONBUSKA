from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, ListView, CreateView
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .models import Parametre, Magasin
from .forms import ParametresForm, ParametresEditForm, MagasinCreateForm


class ParametresView(LoginRequiredMixin, FormView):
    model = Parametre
    context_object_name = 'parametres'
    form_class = ParametresForm
    template_name = 'parametres/parametres.html'

    @staticmethod
    def get_parametres():
        params = Parametre.objects.get(code='Params')
        return params

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parametres'] = self.get_parametres()
        return context

    def get_initial(self):
        initial = super().get_initial()
        params = self.get_parametres()
        initial['sigle'] = params.sigle
        initial['societe'] = params.societe
        initial['rccm'] = params.rccm
        initial['idnat'] = params.idnat
        initial['impot'] = params.impot
        initial['tva'] = params.tva
        initial['adresse'] = params.adresse
        initial['pays'] = params.pays
        initial['ville'] = params.ville
        initial['telephone'] = params.telephone
        initial['email'] = params.email
        return initial


class ParametresUpdateView(LoginRequiredMixin, UpdateView):
    model = Parametre
    context_object_name = 'parametres'
    form_class = ParametresEditForm
    success_url = reverse_lazy('parametres')
    template_name = 'parametres/parametres_form.html'


class MagasinsView(LoginRequiredMixin, ListView):
    model = Magasin
    context_object_name = 'liste_magasins'
    template_name = 'parametres/magasins.html'


class MagasinCreateView(LoginRequiredMixin, CreateView):
    model = Magasin
    template_name = 'parametres/magasin_create_form.html'
    form_class = MagasinCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creation magasin'
        context['title_page'] = 'Create'
        context['title_form'] = "Formulaire de creation d'un magasin"
        return context


class MagasinUpdateView(LoginRequiredMixin, UpdateView):
    model = Magasin
    template_name = 'parametres/magasin_create_form.html'
    form_class = MagasinCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modification magasin'
        context['title_page'] = 'Update'
        context['title_form'] = 'Formulaire de modification du magasin #{}'.format(self.get_object().nom)
        return context
