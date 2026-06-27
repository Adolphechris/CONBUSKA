from users.permissions import RoleRequiredMixin, ROLE_ADMIN
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django_filters.views import FilterView
from .models import Creancier, Debiteur
from .forms import CreancierCreateForm, DebiteurCreateForm
from .filters import CreancierFilter, DebiteurFilter


class CreanciersView(RoleRequiredMixin, FilterView):
    allowed_roles = [ROLE_ADMIN]
    model = Creancier
    context_object_name = 'liste_creanciers'
    template_name = 'creanciers/creanciers.html'
    filterset_class = CreancierFilter

    def get_queryset(self):
        return Creancier.objects.all().order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        creanciers = self.get_queryset()
        context['total_solde_usd'] = sum(creancier.solde_usd() for creancier in creanciers)
        context['total_solde'] = sum(creancier.solde() for creancier in creanciers)
        return context


class CreancierDetailsView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = Creancier
    context_object_name = 'creancier'
    template_name = 'creanciers/creancier_details.html'


class CreancierCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = Creancier
    template_name = 'creanciers/creancier_create_form.html'
    form_class = CreancierCreateForm


class CreancierUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Creancier
    template_name = 'creanciers/creancier_create_form.html'
    form_class = CreancierCreateForm


class CreancierDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [ROLE_ADMIN]
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


class DebiteursView(RoleRequiredMixin, FilterView):
    allowed_roles = [ROLE_ADMIN]
    model = Debiteur
    context_object_name = 'liste_debiteurs'
    template_name = 'creanciers/debiteurs.html'
    filterset_class = DebiteurFilter

    def get_queryset(self):
        return Debiteur.objects.all().order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        debiteurs = self.get_queryset()
        context['total_solde_usd'] = sum(debiteur.solde_usd() for debiteur in debiteurs)
        context['total_solde'] = sum(debiteur.solde() for debiteur in debiteurs)
        return context


class DebiteurDetailsView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = Debiteur
    context_object_name = 'debiteur'
    template_name = 'creanciers/debiteur_details.html'


class DebiteurCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = Debiteur
    template_name = 'creanciers/debiteur_create_form.html'
    form_class = DebiteurCreateForm


class DebiteurUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Debiteur
    template_name = 'creanciers/debiteur_create_form.html'
    form_class = DebiteurCreateForm


class DebiteurDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [ROLE_ADMIN]
    model = Debiteur
    template_name = 'creanciers/debiteur_confirm_delete.html'
    success_url = reverse_lazy('debiteurs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer un débiteur'
        context['message'] = 'Voulez-vous supprimer le débiteur {} ?'.format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context


class CreancierRelevePdfView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        from utils.pdf_generator import DocumentGenerator
        creancier = get_object_or_404(Creancier, pk=pk)
        prets     = list(creancier.prets())
        paiements = list(creancier.paiements())

        debit_rows = [
            [
                str(i + 1),
                p.mouvement_caisse.date_mouvement.strftime('%d/%m/%Y'),
                f'{float(p.mouvement_caisse.montant):,.0f}',
            ]
            for i, p in enumerate(prets)
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
            filename=f'releve_creancier_{creancier.code}.pdf',
            title=f'RELEVÉ DE COMPTE — CRÉANCIER — {creancier.nom.upper()}',
        )
        return gen.generate_releve_compte(
            tiers_info={
                'nom': creancier.nom,
                'code': creancier.code,
                'type': 'Créancier',
                'telephone': creancier.telephone,
                'email': creancier.email,
                'adresse': creancier.adresse,
                'ville': creancier.ville,
            },
            debit_label='Prêts reçus',
            credit_label='Remboursements effectués',
            debit_headers=['N°', 'Date', 'Montant (FC)'],
            debit_rows=debit_rows,
            credit_rows=credit_rows,
            total_debit=float(creancier.total_prets()),
            total_credit=float(creancier.total_paiements()),
        )


class DebiteurRelevePdfView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        from utils.pdf_generator import DocumentGenerator
        debiteur  = get_object_or_404(Debiteur, pk=pk)
        prets     = list(debiteur.prets())
        paiements = list(debiteur.paiements())

        debit_rows = [
            [
                str(i + 1),
                p.mouvement_caisse.date_mouvement.strftime('%d/%m/%Y'),
                f'{float(p.mouvement_caisse.montant):,.0f}',
            ]
            for i, p in enumerate(prets)
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
            filename=f'releve_debiteur_{debiteur.code}.pdf',
            title=f'RELEVÉ DE COMPTE — DÉBITEUR — {debiteur.nom.upper()}',
        )
        return gen.generate_releve_compte(
            tiers_info={
                'nom': debiteur.nom,
                'code': debiteur.code,
                'type': 'Débiteur',
                'telephone': debiteur.telephone,
                'email': debiteur.email,
                'adresse': debiteur.adresse,
                'ville': debiteur.ville,
            },
            debit_label='Prêts accordés',
            credit_label='Remboursements reçus',
            debit_headers=['N°', 'Date', 'Montant (FC)'],
            debit_rows=debit_rows,
            credit_rows=credit_rows,
            total_debit=float(debiteur.total_prets()),
            total_credit=float(debiteur.total_paiements()),
        )

