from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Client, PaiementClient
from .forms import ClientCreateForm


class ClientsView(LoginRequiredMixin, ListView):
    model = Client
    context_object_name = 'liste_clients'
    template_name = 'clients/clients.html'


class ClientDetailsView(LoginRequiredMixin, DetailView):
    model = Client
    context_object_name = 'client'
    template_name = 'clients/client_details.html'

    def get_paiements(self):
        paiements = PaiementClient.objects.filter(client=self.get_object())
        return paiements

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paiements'] = self.get_paiements()
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    template_name = 'clients/client_create_form.html'
    form_class = ClientCreateForm


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    template_name = 'clients/client_create_form.html'
    form_class = ClientCreateForm


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer un client'
        context['message'] = 'Voulez-vous supprimer le client {} ?'.format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context
