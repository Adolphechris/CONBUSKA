"""
produits/views/transfert_stock.py

Vues du module transferts de stock.
Chaque vue appelle exactement un service et délègue toute la logique métier.
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.http import require_GET
from django.views.generic import ListView

from produits.exceptions import (
    ReservationVideError,
    StockInsuffisantError,
    TransfertDejaValideError,
    TransfertInactifError,
)
from produits.forms import (
    ArticleTransfertAddForm,
    ArticleTransfertUpdateForm,
    TransfertCreateForm,
)
from produits.inputs import (
    TransfertCreateInput,
    TransfertLigneAddInput,
    TransfertLigneUpdateInput,
)
from produits.models import DetailsTransfertStock, TransfertStock
from produits.selectors import get_transfert, liste_details_transfert, liste_transferts
from produits.services.transfert_service import (
    ajouter_ligne_transfert,
    creer_transfert,
    modifier_ligne_transfert,
    supprimer_ligne_transfert,
    valider_transfert,
)
from users.permissions import ROLE_ADMIN, RoleRequiredMixin, user_has_role


# ── Helper interne ──────────────────────────────────────────────────────────────

def _render_table(request, transfert: TransfertStock) -> HttpResponse:
    """Renvoie le fragment HTML de la table des lignes du transfert."""
    html = render_to_string(
        "produits/transfert/partials/_table.html",
        {
            "transfert": transfert,
            "details_transfert": liste_details_transfert(transfert_id=transfert.pk),
        },
        request=request,
    )
    return HttpResponse(html)


# ── Vues ────────────────────────────────────────────────────────────────────────

class HistoriqueTransfertStockView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = TransfertStock
    context_object_name = "historique_transfert_stock"
    template_name = "produits/transfert/transferts.html"

    def get_queryset(self):
        return liste_transferts()


class TransfertCreateView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]
    template_name = "produits/transfert/transfert_form.html"

    def get(self, request):
        form = TransfertCreateForm()
        return render(request, self.template_name, self._ctx(form))

    def post(self, request):
        form = TransfertCreateForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(form))

        data = TransfertCreateInput(
            magasin_source_id=form.cleaned_data["magasin_source"].pk,
            magasin_destination_id=form.cleaned_data["magasin_destination"].pk,
        )
        result = creer_transfert(data=data, current_user=request.user)
        return redirect("transfert_details", pk=result.transfert.pk)

    def _ctx(self, form):
        return {
            "form": form,
            "title": "Création nouveau transfert",
            "title_form": "Formulaire de création d'un nouveau transfert de stock",
            "cancel_url": reverse("transferts_stock"),
        }


class TransfertDetailView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]
    template_name = "produits/transfert/transfert_details.html"

    def get(self, request, pk):
        transfert = get_transfert(transfert_id=pk)
        return render(request, self.template_name, {
            "transfert": transfert,
            "details_transfert": liste_details_transfert(transfert_id=pk),
            "add_form": ArticleTransfertAddForm(),
        })


@login_required
@require_GET
def get_form_update_transfert(request, pk):
    # FBV : vue GET-only, aucun mixin nécessaire, retourne un fragment HTMX
    if not user_has_role(request.user, ROLE_ADMIN):
        raise PermissionDenied
    instance = get_object_or_404(DetailsTransfertStock, pk=pk)
    form = ArticleTransfertUpdateForm(instance=instance)
    return render(
        request,
        "produits/transfert/partials/_update_form.html",
        {"form": form, "detail_transfert_pk": instance.pk},
    )


class TransfertLineCreateView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def post(self, request, pk):
        if not request.headers.get("HX-Request"):
            return HttpResponse(status=400)

        transfert = get_object_or_404(TransfertStock, pk=pk)
        form = ArticleTransfertAddForm(request.POST)

        if not form.is_valid():
            return self._form_error(request, form, transfert)

        data = TransfertLigneAddInput(
            transfert_id=pk,
            article_id=form.cleaned_data["article"].pk,
            qte=form.cleaned_data["qte"],
        )

        try:
            result = ajouter_ligne_transfert(data=data)
        except (TransfertInactifError, StockInsuffisantError) as exc:
            form.add_error(None, str(exc))
            return self._form_error(request, form, transfert)

        return _render_table(request, result.transfert)

    def _form_error(self, request, form, transfert) -> HttpResponse:
        response = render(
            request,
            "produits/transfert/partials/_add_form.html",
            {"form": form, "transfert": transfert},
            status=422,
        )
        response["HX-Retarget"] = "#addFormContainer"
        response["HX-Reswap"] = "innerHTML"
        return response


class TransfertLineUpdateView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def post(self, request, pk):
        # pk dans l'URL = pk du DetailsTransfertStock (convention du template)
        if not request.headers.get("HX-Request"):
            return HttpResponse(status=400)

        detail = get_object_or_404(DetailsTransfertStock, pk=pk)
        form = ArticleTransfertUpdateForm(request.POST, instance=detail)

        if not form.is_valid():
            return self._form_error(request, form, pk)

        data = TransfertLigneUpdateInput(
            detail_id=detail.pk,
            transfert_id=detail.transfert_id,
            qte=form.cleaned_data["qte"],
        )

        try:
            result = modifier_ligne_transfert(data=data)
        except (TransfertInactifError, StockInsuffisantError) as exc:
            form.add_error(None, str(exc))
            return self._form_error(request, form, pk)

        return _render_table(request, result.transfert)

    def _form_error(self, request, form, detail_pk) -> HttpResponse:
        response = render(
            request,
            "produits/transfert/partials/_update_form.html",
            {"form": form, "detail_transfert_pk": detail_pk},
            status=422,
        )
        response["HX-Retarget"] = "#updateFormContainer"
        response["HX-Reswap"] = "innerHTML"
        return response


class TransfertLineDeleteView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]
    template_name = "produits/transfert/transfert_confirm_delete.html"

    def get(self, request, transfert_pk, pk):
        detail = get_object_or_404(
            DetailsTransfertStock, pk=pk, transfert_id=transfert_pk
        )
        return render(request, self.template_name, {
            "title": "Supprimer un article du transfert",
            "message": (
                f"Voulez-vous supprimer l'article {detail.article} du transfert ?"
            ),
            "submit_icon": "fa fa-check",
            "submit_label": "Valider",
            "transfert": detail.transfert,
            "object": detail,
        })

    def post(self, request, transfert_pk, pk):
        # Vérifie l'appartenance avant suppression
        get_object_or_404(DetailsTransfertStock, pk=pk, transfert_id=transfert_pk)
        transfert = supprimer_ligne_transfert(detail_id=pk)

        if request.headers.get("HX-Request") == "true":
            return _render_table(request, transfert)

        return redirect("transfert_details", pk=transfert.pk)


class TransfertSaveView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]
    template_name = "produits/transfert/transfert_confirm_save.html"

    def get(self, request, pk):
        transfert = get_object_or_404(TransfertStock, pk=pk)
        return render(request, self.template_name, self._ctx(transfert))

    def post(self, request, pk):
        try:
            valider_transfert(transfert_id=pk)
        except (TransfertDejaValideError, ReservationVideError) as exc:
            transfert = get_object_or_404(TransfertStock, pk=pk)
            ctx = self._ctx(transfert)
            ctx["error"] = str(exc)
            return render(request, self.template_name, ctx, status=422)

        return redirect(reverse_lazy("transferts_stock"))

    def _ctx(self, transfert: TransfertStock) -> dict:
        return {
            "title": "Enregistrer un transfert",
            "message": (
                f"Voulez-vous enregistrer et valider le transfert "
                f"{transfert.numero} ?"
            ),
            "submit_icon": "fa fa-check",
            "submit_label": "Valider",
            "transfert": transfert,
        }
