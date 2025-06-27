from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Creancier
from .forms import CreancierCreateForm


class CreanciersView(LoginRequiredMixin, ListView):
    model = Creancier
    context_object_name = 'liste_creanciers'
    template_name = 'creanciers/creanciers.html'


class CreancierDetailsView(LoginRequiredMixin, DetailView):
    model = Creancier
    context_object_name = 'creancier'
    template_name = 'creanciers/creancier_details.html'

    def get_paiements(self):
        paiements = ''
        return paiements

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paiements'] = self.get_paiements()
        return context


class CreancierCreateView(LoginRequiredMixin, CreateView):
    model = Creancier
    template_name = 'creanciers/creancier_create_form.html'
    form_class = CreancierCreateForm


class CreancierUpdateView(LoginRequiredMixin, UpdateView):
    model = Creancier
    template_name = 'creanciers/creancier_create_form.html'
    form_class = CreancierCreateForm


class CreancierDeleteView(LoginRequiredMixin, DeleteView):
    model = Creancier
    template_name = 'creanciers/creancier_confirm_delete.html'
    success_url = reverse_lazy('clients')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer un creancier'
        context['message'] = 'Voulez-vous supprimer le creancier {} ?'.format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context

