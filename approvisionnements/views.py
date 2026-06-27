from users.permissions import RoleRequiredMixin, ROLE_ADMIN, user_has_role
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, View
from django.shortcuts import redirect, get_object_or_404, render, HttpResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.core.exceptions import PermissionDenied
from .models import Approvisionnement, DetailsApprovisionnement
from .forms import ApprovisionnementCreateForm, ArticleApprovisionnementAddForm, ArticleApprovisionnementUpdateForm
from .services import ApprovisionnementService, FraisService


class ApprovisionnementsView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = Approvisionnement
    context_object_name = 'liste_approvisionnements'
    template_name = 'approvisionnements/approvisionnements.html'
    ordering = ['-numero']


class ApprovisionnementCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = Approvisionnement
    template_name = 'approvisionnements/approvisionnement_form.html'
    form_class = ApprovisionnementCreateForm

    def form_valid(self, form, *args, **kwargs):
        approvisionnement = form.save(commit=False)
        approvisionnement.cree_par = self.request.user
        approvisionnement.save()
        return redirect('approvisionnement_details', pk=approvisionnement.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creation nouvel approvisionnement'
        context['title_form'] = "Formulaire de creation d'un nouvel approvisionnement"
        context['cancel_url'] = reverse('approvisionnements')
        return context


class ApprovisionnementUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Approvisionnement
    template_name = 'approvisionnements/approvisionnement_form.html'
    form_class = ApprovisionnementCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modification approvisionnement'
        context['title_form'] = "Formulaire de modification de l'approvisionnement #{}".format(self.get_object().numero)
        context['cancel_url'] = reverse('approvisionnement_details', args=[self.get_object().pk])
        return context


class ApprovisionnementDeleteView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]
    model = Approvisionnement
    template_name = 'approvisionnements/approvisionnement_confirm_delete.html'
    success_url = reverse_lazy('approvisionnements')

    def get(self, request, pk):
        approvisionnement = get_object_or_404(Approvisionnement, pk=pk)

        context = {
            "title": "Suppression approvisionnement",
            "message": f"Voulez-vous supprimer l'approvisionnement {approvisionnement.numero} ?",
            "submit_icon": "fa fa-check",
            "submit_label": "Valider",
            "approvisionnement": approvisionnement,
        }

        return render(
            request,
            'approvisionnements/approvisionnement_confirm_delete.html',
            context
        )

    def post(self, request, pk):
        approvisionnement = get_object_or_404(Approvisionnement, pk=pk)
        ApprovisionnementService.supprimer(approvisionnement=approvisionnement)

        if request.headers.get("HX-Request"):
            # Redirection vers la liste des approvisionnements
            response = HttpResponse()
            response["HX-Redirect"] = reverse('approvisionnements')
            return response

        return redirect("approvisionnements")


class ApprovisionnementSaveView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    model = Approvisionnement
    template_name = 'approvisionnements/approvisionnement_confirm_save.html'
    success_url = reverse_lazy('approvisionnements')

    def get_approvisionnement(self):
        return get_object_or_404(Approvisionnement, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Enregistrer un approvisionnement'
        context['message'] = "Voulez-vous enregistrer l'approvisionnement {} ?".format(self.get_approvisionnement().numero)
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context

    def post(self, request, *args, **kwargs):
        approvisionnement = self.get_approvisionnement()
        try:
            ApprovisionnementService.valider(
                approvisionnement=approvisionnement,
                user=request.user
            )
        except ValidationError as e:
            return HttpResponse(str(e), status=400)
        return redirect(self.success_url)


@login_required
@require_GET
def get_update_form(request, pk):
    if not user_has_role(request.user, ROLE_ADMIN):
        raise PermissionDenied
    instance = get_object_or_404(DetailsApprovisionnement, pk=pk)
    form = ArticleApprovisionnementUpdateForm(instance=instance)
    return render(request, "approvisionnements/partials/update_form.html", {
        "update_form": form,
        "appro_pk": instance.approvisionnement.pk,
        "detail_appro_pk": pk,
        "article_nom": instance.article.designation,
        "fournisseur_nom": str(instance.fournisseur),
    })


class ApprovisionnementDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = Approvisionnement
    context_object_name = "approvisionnement"
    template_name = "approvisionnements/approvisionnement_details.html"

    @cached_property
    def details_approvisionnement(self):
        return (
            DetailsApprovisionnement.objects
            .filter(approvisionnement=self.object)
            .select_related("article", "fournisseur")
            .order_by("pk")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["details_approvisionnement"] = self.details_approvisionnement
        context["add_form"] = ArticleApprovisionnementAddForm()

        # Dual currency: passer les valeurs USD de l'approvisionnement
        appro = self.object
        context["approvisionnement_valeur_usd"] = getattr(appro, 'valeur_usd', None)
        context["approvisionnement_taux"] = appro.taux

        details_with_usd = []
        for detail in self.details_approvisionnement:
            details_with_usd.append({
                'pk': detail.pk,
                'article': detail.article,
                'fournisseur': detail.fournisseur,
                'qte': detail.qte,
                'prix': detail.prix,
                'prix_total': detail.prix_total,
                'valeur_usd': detail.valeur_usd,
                'taux_creation': detail.taux_creation,
                'date_peremption': detail.date_peremption,
            })
        context["details_approvisionnement_usd"] = details_with_usd

        return context


class ApprovisionnementShowDetailsView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    """
    Vue read-only pour consulter une fiche d'approvisionnement depuis le module fournisseurs.
    """
    model = Approvisionnement
    context_object_name = "approvisionnement"
    template_name = "approvisionnements/approvisionnement_show_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approvisionnement = self.object
        context["approvisionnement"] = approvisionnement
        context["details_approvisionnement"] = (
            DetailsApprovisionnement.objects
            .filter(approvisionnement=approvisionnement)
            .select_related("article", "fournisseur")
            .order_by("pk")
        )
        return context

def is_htmx(request):
    return request.headers.get("HX-Request", "").lower() == "true"


class ApprovisionnementLineTableMixin:

    def _render_table(self, request, approvisionnement):
        html = render_to_string(
            "approvisionnements/partials/lines_table.html",
            {
                "approvisionnement": approvisionnement,
                "details_approvisionnement": (
                    DetailsApprovisionnement.objects
                    .filter(approvisionnement=approvisionnement)
                    .select_related("article", "fournisseur")
                ),
            },
            request=request,
        )
        return HttpResponse(html)


class ApprovisionnementLineCreateView(RoleRequiredMixin, ApprovisionnementLineTableMixin, View):

    allowed_roles = [ROLE_ADMIN]
    def post(self, request, pk):
        if not is_htmx(request):
            return JsonResponse({"error": "HTMX required"}, status=400)

        approvisionnement = get_object_or_404(Approvisionnement, pk=pk)
        form = ArticleApprovisionnementAddForm(request.POST)

        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)

        with transaction.atomic():
            detail = form.save(commit=False)
            detail.approvisionnement = approvisionnement
            detail.article = form.cleaned_data['article']
            detail.fournisseur = form.cleaned_data['fournisseur']
            detail = detail.add()

            # Enregistrement des frais
            FraisService.save_frais(detail, form.cleaned_data)

        return self._render_table(request, approvisionnement)


class ApprovisionnementLineUpdateView(RoleRequiredMixin, ApprovisionnementLineTableMixin, View):

    allowed_roles = [ROLE_ADMIN]
    def post(self, request, pk):
        if not request.headers.get("HX-Request"):
            return JsonResponse({"error": "HTMX required"}, status=400)

        detail = get_object_or_404(
            DetailsApprovisionnement,
            pk=request.POST.get('id')
        )

        approvisionnement = detail.approvisionnement

        # Capture l'article et le fournisseur AVANT que le form ne les écrase.
        article_verrouille = detail.article
        fournisseur_verrouille = detail.fournisseur

        form = ArticleApprovisionnementUpdateForm(
            request.POST,
            instance=detail
        )

        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)

        with transaction.atomic():
            detail = form.save(commit=False)
            # Réaffectation explicite : article et fournisseur ne peuvent
            # pas changer, quelle que soit la valeur reçue en POST.
            detail.article = article_verrouille
            detail.fournisseur = fournisseur_verrouille
            detail.update_appro()

            # Enregistrement des frais
            FraisService.save_frais(detail, form.cleaned_data)

        return self._render_table(request, approvisionnement)


class ArticleApprovisionnementDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [ROLE_ADMIN]
    model = DetailsApprovisionnement
    template_name = 'approvisionnements/approvisionnement_article_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['title'] = "Supprimer un article de l'approvisionnement"
        context['message'] = f"Voulez-vous supprimer l'article {obj.article} de l'approvisionnement ?"
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        context['approvisionnement'] = obj.approvisionnement
        return context

    def get_success_url(self):
        return reverse('approvisionnement_details', kwargs={'pk': self.object.approvisionnement.pk})

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        appro = self.object.approvisionnement

        self.object.delete()

        if request.headers.get('HX-Request') == 'true':
            details = (
                DetailsApprovisionnement.objects
                .filter(approvisionnement=appro)
                .prefetch_related("frais__type_frais")
            )

            table_html = render_to_string(
                "approvisionnements/partials/lines_table.html",
                {'details_approvisionnement': details, 'approvisionnement': appro},
                request=request,
            )
            # On retourne le tableau avec un swap OOB sur linesTableContainer
            # ET un swap vide sur modalContent pour fermer
            response = HttpResponse(
                f'<div id="linesTableContainer" hx-swap-oob="innerHTML">{table_html}</div>'
                f'<div id="modalContent" hx-swap-oob="innerHTML"></div>'
            )
            response['HX-Trigger'] = 'closeModal'
            return response

        return redirect(self.get_success_url())


class BonApproPdfView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def get(self, request, pk):
        from utils.pdf_generator import DocumentGenerator
        appro = get_object_or_404(Approvisionnement, pk=pk)
        details = (
            DetailsApprovisionnement.objects
            .filter(approvisionnement=appro)
            .select_related('article', 'fournisseur')
            .prefetch_related('frais__type_frais')
            .order_by('pk')
        )
        gen = DocumentGenerator(
            filename=f'bon_appro_{appro.numero}.pdf',
            title=f'Bon d\'approvisionnement N° {appro.numero}',
        )
        return gen.generate_bon_appro(appro=appro, details=details)
