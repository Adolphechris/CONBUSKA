"""
commandes/views.py

Toutes les vues du module commandes.
Chaque vue délègue au service (écriture) ou au selector (lecture).
Aucune logique métier ici.
"""

from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from users.permissions import ROLE_ADMIN, RoleRequiredMixin

from .exceptions import CommandeDejaClotureError
from .forms import ArticleCommandeAddForm, ArticleCommandeUpdateForm, CommandeCreateForm
from .inputs import (
    ArticleCommandeAddInput,
    ArticleCommandeUpdateInput,
    CommandeCreateInput,
    CommandeUpdateInput,
)
from .models import Commande, DetailsCommande
from .selectors import (
    liste_commandes,
    liste_details_commande,
    total_commande,
)
from .services import (
    ajouter_article_commande,
    annuler_commande,
    cloturer_commande,
    creer_commande,
    modifier_article_commande,
    modifier_commande,
    supprimer_article_commande,
    valider_commande,
    transformer_commande,
)


def is_htmx(request) -> bool:
    return request.headers.get("HX-Request", "").lower() == "true"


# ── List ──────────────────────────────────────────────────────────────────────

class CommandesView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    context_object_name = 'liste_commandes'
    template_name = 'commandes/commandes.html'

    def get_queryset(self):
        return liste_commandes()


# ── Create ────────────────────────────────────────────────────────────────────

class CommandeCreateView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'commandes/commande_form.html'

    def _context(self, form):
        return {
            'form': form,
            'title': 'Nouvelle commande',
            'title_form': "Formulaire de création d'une commande",
            'cancel_url': reverse('commandes'),
        }

    def get(self, request):
        return render(request, self.template_name, self._context(CommandeCreateForm()))

    def post(self, request):
        form = CommandeCreateForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._context(form))
        devise = form.cleaned_data.get('devise')
        data = CommandeCreateInput(
            date_commande=form.cleaned_data['date_commande'],
            fournisseur_id=form.cleaned_data['fournisseur'].pk,
            taux=form.cleaned_data['taux'],
            devise_id=devise.pk if devise else None,
        )
        result = creer_commande(data=data, current_user=request.user)
        return redirect('commande_details', pk=result.commande.pk)


# ── Update ────────────────────────────────────────────────────────────────────

class CommandeUpdateView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'commandes/commande_form.html'

    def _context(self, form, commande):
        return {
            'form': form,
            'title': 'Modifier commande',
            'title_form': f'Modification de la commande #{commande.numero}',
            'cancel_url': reverse('commande_details', args=[commande.pk]),
        }

    def get(self, request, pk):
        commande = get_object_or_404(Commande, pk=pk)
        form = CommandeCreateForm(instance=commande)
        return render(request, self.template_name, self._context(form, commande))

    def post(self, request, pk):
        commande = get_object_or_404(Commande, pk=pk)
        form = CommandeCreateForm(request.POST, instance=commande)
        if not form.is_valid():
            return render(request, self.template_name, self._context(form, commande))
        devise = form.cleaned_data.get('devise')
        data = CommandeUpdateInput(
            commande_id=pk,
            date_commande=form.cleaned_data['date_commande'],
            fournisseur_id=form.cleaned_data['fournisseur'].pk,
            taux=form.cleaned_data['taux'],
            devise_id=devise.pk if devise else None,
        )
        result = modifier_commande(data=data, current_user=request.user)
        return redirect('commande_details', pk=result.commande.pk)


# ── Delete (logical) ──────────────────────────────────────────────────────────

class CommandeDeleteView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        commande = get_object_or_404(Commande, pk=pk)
        return render(request, 'commandes/commande_confirm_delete.html', {
            'title': 'Annuler une commande',
            'message': f'Voulez-vous annuler la commande {commande.numero} ?',
            'submit_icon': 'fa fa-check',
            'submit_label': 'Valider',
            'commande': commande,
        })

    def post(self, request, pk):
        commande = get_object_or_404(Commande, pk=pk)
        annuler_commande(commande_id=commande.pk, current_user=request.user)
        if is_htmx(request):
            response = HttpResponse()
            response['HX-Redirect'] = reverse('commandes')
            return response
        return redirect('commandes')


# ── Close (clôturer) ──────────────────────────────────────────────────────────

class CommandeSaveView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'commandes/commande_confirm_save.html'

    def _get_commande(self):
        return get_object_or_404(Commande, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        commande = self._get_commande()
        context['title'] = 'Enregistrer une commande'
        context['message'] = f'Voulez-vous enregistrer la commande {commande.numero} ?'
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context

    def post(self, request, *args, **kwargs):
        commande = self._get_commande()
        try:
            cloturer_commande(commande_id=commande.pk, current_user=request.user)
        except CommandeDejaClotureError:
            pass  # déjà clôturée — rediriger quand même
        return redirect('commandes')


# ── Detail ────────────────────────────────────────────────────────────────────

class CommandeDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = Commande
    context_object_name = 'commande'
    template_name = 'commandes/commande_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        commande = self.object
        context['details_commande'] = liste_details_commande(commande=commande)
        context['add_form'] = ArticleCommandeAddForm()
        context['total'] = total_commande(commande=commande)
        return context


# ── HTMX Line Table helper ────────────────────────────────────────────────────

class CommandeLineTableMixin:
    def _render_table(self, request, commande: Commande) -> HttpResponse:
        html = render_to_string(
            'commandes/partials/lines_table.html',
            {
                'commande': commande,
                'details_commande': liste_details_commande(commande=commande),
                'total': total_commande(commande=commande),
            },
            request=request,
        )
        return HttpResponse(html)


# ── HTMX Line Create ──────────────────────────────────────────────────────────

class CommandeLineCreateView(RoleRequiredMixin, CommandeLineTableMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def post(self, request, pk):
        if not is_htmx(request):
            return JsonResponse({'error': 'HTMX required'}, status=400)

        commande = get_object_or_404(Commande, pk=pk)
        form = ArticleCommandeAddForm(request.POST)

        if not form.is_valid():
            html = render_to_string(
                'commandes/partials/add_form.html',
                {'add_form': form, 'commande': commande},
                request=request,
            )
            response = HttpResponse(html)
            response['HX-Retarget'] = '#addFormContainer'
            response['HX-Reswap'] = 'innerHTML'
            return response

        data = ArticleCommandeAddInput(
            commande_id=commande.pk,
            article_id=form.cleaned_data['article'].pk,
            qte=form.cleaned_data['qte'],
            prix=form.cleaned_data['prix'] or Decimal('0'),
        )
        ajouter_article_commande(data=data, current_user=request.user)
        return self._render_table(request, commande)


# ── HTMX Line Update ──────────────────────────────────────────────────────────

class CommandeLineUpdateView(RoleRequiredMixin, CommandeLineTableMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def post(self, request, pk):
        if not is_htmx(request):
            return JsonResponse({'error': 'HTMX required'}, status=400)

        detail = get_object_or_404(DetailsCommande, pk=request.POST.get('id'))
        commande = detail.commande
        article_locked = detail.article

        form = ArticleCommandeUpdateForm(request.POST, instance=detail)
        if not form.is_valid():
            html = render_to_string(
                'commandes/partials/update_form.html',
                {
                    'update_form': form,
                    'commande_pk': commande.pk,
                    'detail_pk': detail.pk,
                    'article_nom': article_locked.designation,
                },
                request=request,
            )
            response = HttpResponse(html)
            response['HX-Retarget'] = '#updateFormContainer'
            response['HX-Reswap'] = 'innerHTML'
            return response

        data = ArticleCommandeUpdateInput(
            detail_id=detail.pk,
            qte=form.cleaned_data['qte'],
            prix=form.cleaned_data['prix'],
        )
        modifier_article_commande(data=data, current_user=request.user)
        response = self._render_table(request, commande)
        response['HX-Trigger'] = 'lineUpdated'
        return response


# ── HTMX Get Update Form ──────────────────────────────────────────────────────

class CommandeUpdateFormView(RoleRequiredMixin, View):
    """Retourne le formulaire de modification d'une ligne (GET HTMX uniquement)."""
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        detail = get_object_or_404(DetailsCommande, pk=pk)
        form = ArticleCommandeUpdateForm(instance=detail)
        return render(request, 'commandes/partials/update_form.html', {
            'update_form': form,
            'commande_pk': detail.commande.pk,
            'detail_pk': pk,
            'article_nom': detail.article.designation,
        })


# ── Delete Article ────────────────────────────────────────────────────────────

class ArticleCommandeDeleteView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, commande_pk, pk):
        detail = get_object_or_404(DetailsCommande, pk=pk)
        commande = get_object_or_404(Commande, pk=commande_pk)
        return render(request, 'commandes/commande_confirm_delete_article.html', {
            'title': 'Supprimer un article',
            'message': f'Supprimer "{detail.article.designation}" de la commande ?',
            'submit_label': 'Supprimer',
            'submit_icon': 'fa fa-trash-o',
            'commande': commande,
            'detail': detail,
        })

    def post(self, request, commande_pk, pk):
        detail = get_object_or_404(DetailsCommande, pk=pk)
        commande = detail.commande
        supprimer_article_commande(detail_id=pk, current_user=request.user)
        if is_htmx(request):
            html = render_to_string(
                'commandes/partials/lines_table.html',
                {
                    'commande': commande,
                    'details_commande': liste_details_commande(commande=commande),
                    'total': total_commande(commande=commande),
                },
                request=request,
            )
            return HttpResponse(html)
        return redirect('commande_details', pk=commande.pk)


# ── Workflow: Validation ──────────────────────────────────────────────────────

class CommandeValiderView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'commandes/commande_confirm_valider.html'

    def _get_commande(self):
        return get_object_or_404(Commande, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        commande = self._get_commande()
        context['title'] = 'Valider la commande'
        context['message'] = f'Voulez-vous valider la commande {commande.numero} ?'
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        context['commande'] = commande
        return context

    def post(self, request, *args, **kwargs):
        commande = self._get_commande()
        try:
            valider_commande(commande_id=commande.pk, current_user=request.user)
        except Exception as e:
            # Gérer l'erreur (à améliorer avec messages)
            pass
        if is_htmx(request):
            response = HttpResponse()
            response['HX-Redirect'] = reverse('commande_details', args=[commande.pk])
            return response
        return redirect('commande_details', pk=commande.pk)


# ── Workflow: Transformation en approvisionnement ────────────────────────────

class CommandeTransformerView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'commandes/commande_confirm_transformer.html'

    def _get_commande(self):
        return get_object_or_404(Commande, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        commande = self._get_commande()
        context['title'] = 'Transformer en approvisionnement'
        context['message'] = (
            f'Voulez-vous transformer la commande {commande.numero} '
            f'en approvisionnement ?'
        )
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Transformer'
        context['commande'] = commande
        return context

    def post(self, request, *args, **kwargs):
        commande = self._get_commande()
        try:
            approv = transformer_commande(
                commande_id=commande.pk,
                current_user=request.user,
            )
            # Rediriger vers l'approvisionnement créé
            redirect_url = reverse('approvisionnement_details', args=[approv.pk])
        except Exception as e:
            # Gérer l'erreur
            redirect_url = reverse('commande_details', args=[commande.pk])
        
        if is_htmx(request):
            response = HttpResponse()
            response['HX-Redirect'] = redirect_url
            return response
        return redirect(redirect_url)


# ── PDF Views ─────────────────────────────────────────────────────────────────

class BonCommandePdfView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        from utils.pdf_generator import DocumentGenerator
        commande = get_object_or_404(
            Commande.objects.select_related('fournisseur', 'devise'), pk=pk
        )
        details = liste_details_commande(commande=commande)
        gen = DocumentGenerator(
            filename=f'bon_commande_{commande.numero}.pdf',
            title=f'Bon de Commande N° {commande.numero}',
        )
        return gen.generate_bon_commande_fournisseur(commande=commande, details=details, avec_prix=True)


class ProformaPdfView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        from utils.pdf_generator import DocumentGenerator
        commande = get_object_or_404(
            Commande.objects.select_related('fournisseur', 'devise'), pk=pk
        )
        details = liste_details_commande(commande=commande)
        gen = DocumentGenerator(
            filename=f'proforma_{commande.numero}.pdf',
            title=f'Demande de Proforma N° {commande.numero}',
        )
        return gen.generate_bon_commande_fournisseur(commande=commande, details=details, avec_prix=False)
