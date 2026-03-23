from users.permissions import RoleRequiredMixin, ROLE_ADMIN
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404
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


class FournisseurRelevePdfView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        from utils.pdf_generator import DocumentGenerator
        fournisseur = get_object_or_404(Fournisseur, pk=pk)
        mouvements  = list(fournisseur.mouvements())
        paiements   = list(fournisseur.paiements())

        if fournisseur.is_system:
            debit_label   = 'Frais d\'approvisionnement'
            debit_headers = ['N°', 'Date', 'N° Facture', 'Article', 'Qté', 'Frais (FC)']
            debit_rows    = [
                [
                    str(i + 1),
                    m.detail.date_creation.strftime('%d/%m/%Y'),
                    str(m.detail.facture or '—'),
                    str(m.detail.article.designation if m.detail.article else '—'),
                    str(m.detail.qte),
                    f'{float(m.montant):,.0f}',
                ]
                for i, m in enumerate(mouvements)
            ]
        else:
            debit_label   = 'Approvisionnements'
            debit_headers = ['N°', 'Date', 'N° Facture', 'Article', 'Qté', 'PAU (FC)', 'Total (FC)']
            debit_rows    = [
                [
                    str(i + 1),
                    m.date_creation.strftime('%d/%m/%Y'),
                    str(m.facture or '—'),
                    str(m.article.designation if m.article else '—'),
                    str(m.qte),
                    f'{float(m.prix):,.0f}',
                    f'{float(m.prix_total):,.0f}',
                ]
                for i, m in enumerate(mouvements)
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
            filename=f'releve_fournisseur_{fournisseur.code}.pdf',
            title=f'RELEVÉ DE COMPTE — FOURNISSEUR — {fournisseur.nom.upper()}',
        )
        return gen.generate_releve_compte(
            tiers_info={
                'nom': fournisseur.nom,
                'code': fournisseur.code,
                'type': 'Fournisseur Système' if fournisseur.is_system else 'Fournisseur',
                'telephone': fournisseur.telephone,
                'email': fournisseur.email,
                'adresse': fournisseur.adresse,
                'ville': fournisseur.ville,
            },
            debit_label=debit_label,
            credit_label='Paiements effectués',
            debit_headers=debit_headers,
            debit_rows=debit_rows,
            credit_rows=credit_rows,
            total_debit=float(fournisseur.total_mouvements()),
            total_credit=float(fournisseur.total_paiements()),
        )
