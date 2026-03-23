from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django_filters.views import FilterView
from .models import Client
from caisse.models import MouvementCaisseClient
from .forms import ClientCreateForm
from .filters import ClientFilter
from users.permissions import (
    RoleRequiredMixin,
    ROLE_ADMIN, ROLE_FACTURIER, ROLE_CAISSIER, ROLE_GERANT_MAGASIN,
)

_ALL_CLIENT_ROLES = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_CAISSIER, ROLE_GERANT_MAGASIN]


class ClientsView(RoleRequiredMixin, FilterView):
    model = Client
    context_object_name = 'liste_clients'
    template_name = 'clients/clients.html'
    filterset_class = ClientFilter
    allowed_roles = _ALL_CLIENT_ROLES

    def get_queryset(self):
        return Client.objects.all().order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clients = self.get_queryset()
        context['total_solde'] = sum(client.solde() for client in clients)
        return context


class ClientDetailsView(RoleRequiredMixin, DetailView):
    model = Client
    context_object_name = 'client'
    template_name = 'clients/client_details.html'
    allowed_roles = _ALL_CLIENT_ROLES

    def get_paiements(self):
        return MouvementCaisseClient.objects.filter(client=self.get_object())

    def get_context_data(self, **kwargs):
        client = self.get_object()
        context = super().get_context_data(**kwargs)
        context['paiements'] = client.paiements()
        context['factures'] = client.factures()
        context['total_factures'] = client.total_factures()
        context['total_paiements'] = client.total_paiements()
        return context


class ClientCreateView(RoleRequiredMixin, CreateView):
    model = Client
    template_name = 'clients/client_create_form.html'
    form_class = ClientCreateForm
    allowed_roles = [ROLE_ADMIN]


class ClientUpdateView(RoleRequiredMixin, UpdateView):
    model = Client
    template_name = 'clients/client_create_form.html'
    form_class = ClientCreateForm
    allowed_roles = [ROLE_ADMIN]


class ClientDeleteView(RoleRequiredMixin, DeleteView):
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients')
    allowed_roles = [ROLE_ADMIN]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer un client'
        context['message'] = 'Voulez-vous supprimer le client {} ?'.format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context


class ClientRelevePdfView(RoleRequiredMixin, View):
    allowed_roles = _ALL_CLIENT_ROLES

    def get(self, request, pk):
        from utils.pdf_generator import DocumentGenerator
        client   = get_object_or_404(Client, pk=pk)
        factures = list(client.factures())
        paiements = list(client.paiements())

        debit_rows = [
            [
                str(i + 1),
                fc.facture.date_facture.strftime('%d/%m/%Y'),
                f'#{fc.facture.numero}',
                f'{float(fc.facture.total):,.0f}',
            ]
            for i, fc in enumerate(factures)
        ]
        credit_rows = [
            [
                str(i + 1),
                p.mouvement_caisse.date_mouvement.strftime('%d/%m/%Y'),
                f'{float(p.mouvement_caisse.montant):,.0f}',
            ]
            for i, p in enumerate(paiements)
        ]

        gen = DocumentGenerator(
            filename=f'releve_client_{client.code}.pdf',
            title=f'RELEVÉ DE COMPTE — CLIENT — {client.nom.upper()}',
        )
        return gen.generate_releve_compte(
            tiers_info={
                'nom': client.nom,
                'code': client.code,
                'type': 'Client',
                'telephone': client.telephone,
                'email': client.email,
                'adresse': client.adresse,
                'ville': client.ville,
            },
            debit_label='Factures',
            credit_label='Paiements reçus',
            debit_headers=['N°', 'Date', 'N° Facture', 'Total (FC)'],
            debit_rows=debit_rows,
            credit_rows=credit_rows,
            total_debit=float(client.total_factures()),
            total_credit=float(client.total_paiements()),
        )
