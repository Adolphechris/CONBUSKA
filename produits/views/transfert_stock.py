from users.permissions import RoleRequiredMixin, ROLE_ADMIN, user_has_role
from django.views.generic import ListView, DetailView, FormView, View, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render, HttpResponse
from django.utils.functional import cached_property
from django.db import transaction
from django.db.models import Prefetch
from django.core.exceptions import PermissionDenied
from produits.models import TransfertStock, DetailsTransfertStock, ReservationTransfertLot
from produits.forms import TransfertCreateForm, ArticleTransfertAddForm, ArticleTransfertUpdateForm
from produits.services import TransfertService


class HistoriqueTransfertStockView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = TransfertStock
    context_object_name = 'historique_transfert_stock'
    template_name = 'produits/transfert/transferts.html'


class TransfertCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = TransfertStock
    template_name = 'produits/transfert/transfert_form.html'
    form_class = TransfertCreateForm

    def form_valid(self, form, *args, **kwargs):
        transfert = form.save(commit=False)
        transfert.cree_par = self.request.user
        transfert.save()
        return redirect('transfert_details', pk=transfert.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Création nouveau transfert'
        context['title_form'] = "Formulaire de création d'un nouveau transfert de stock"
        context['cancel_url'] = reverse('transferts_stock')
        return context


class TransfertDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = TransfertStock
    context_object_name = "transfert"
    template_name = "produits/transfert/transfert_details.html"

    @cached_property
    def details_transfert(self):
        # On pré-charge les réservations de lots pour éviter le problème N+1
        reservations_queryset = ReservationTransfertLot.objects.order_by('date_peremption')

        return (
            DetailsTransfertStock.objects
            .filter(transfert=self.object)
            .select_related("article", "transfert")
            .prefetch_related(
                Prefetch(
                    'transfert__reservationtransfertlot_set',  # Accès via le transfert
                    queryset=reservations_queryset,
                    to_attr='lots_reserves'  # Nom de la liste attachée à l'objet
                )
            )
            .order_by("article")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["details_transfert"] = self.details_transfert
        context["add_form"] = ArticleTransfertAddForm()
        return context


@login_required
@require_GET
def get_form_update_transfert(request, pk):
    if not user_has_role(request.user, ROLE_ADMIN):
        raise PermissionDenied
    instance = get_object_or_404(DetailsTransfertStock, pk=pk)
    form = ArticleTransfertUpdateForm(instance=instance)
    return render(request, "produits/transfert/partials/_update_form.html",
                  {"form": form, "detail_transfert_pk": instance.pk})


def is_htmx(request):
    return request.headers.get("HX-Request", "").lower() == "true"


class TransfertLineCreateView(RoleRequiredMixin, View):

    allowed_roles = [ROLE_ADMIN]
    def post(self, request, pk):
        if not is_htmx(request):
            return JsonResponse({"error": "HTMX required"}, status=400)

        transfert = get_object_or_404(TransfertStock, pk=pk)
        form = ArticleTransfertAddForm(request.POST)

        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)

        with transaction.atomic():
            detail = form.save(commit=False)
            detail.transfert = transfert
            detail.article = form.cleaned_data['article']
            detail.add()

            ReservationTransfertLot.objects.filter(
                transfert=transfert,
                article=detail.article
            ).delete()

            TransfertService.reserver_fifo(
                transfert=transfert,
                magasin=transfert.magasin_source,
                article=detail.article,
                qte=detail.qte,
            )

        return self._render_table(request, transfert)

    def _render_table(self, request, transfert):
        html = render_to_string(
            "produits/transfert/partials/_table.html",
            {
                "transfert": transfert,
                "details_transfert": (
                    DetailsTransfertStock.objects
                    .filter(transfert=transfert)
                    .select_related("article")
                ),
            },
            request=request,
        )
        return HttpResponse(html)


class TransfertLineUpdateView(RoleRequiredMixin, View):

    allowed_roles = [ROLE_ADMIN]
    def post(self, request, pk):
        if not request.headers.get("HX-Request"):
            return JsonResponse({"error": "HTMX required"}, status=400)

        detail_transfert = get_object_or_404(
            DetailsTransfertStock,
            pk=request.POST.get('detail_transfert_pk')
        )

        transfert = detail_transfert.transfert

        form = ArticleTransfertUpdateForm(
            request.POST,
            instance=detail_transfert
        )

        if not form.is_valid():
            # On renvoie le fragment de formulaire avec les erreurs
            return render(request, "produits/transfert/partials/_update_form.html", {
                "form": form,
                "detail_transfert_pk": pk
            }, status=422)  # 422 Unprocessable Entity

        with transaction.atomic():
            detail = form.save()

            ReservationTransfertLot.objects.filter(
                transfert=transfert,
                article=detail.article
            ).delete()

            TransfertService.reserver_fifo(
                transfert=transfert,
                magasin=transfert.magasin_source,
                article=detail.article,
                qte=detail.qte,
            )

        return self._render_table(request, transfert)

    def _render_table(self, request, transfert):
        print("TRANSFERT ************ ", transfert)
        html = render_to_string(
            "produits/transfert/partials/_table.html",
            {
                "transfert": transfert,
                "details_transfert": (
                    DetailsTransfertStock.objects
                    .filter(transfert=transfert.pk)
                    .select_related("article")
                    .order_by("article")
                ),
            },
            request=request,
        )
        return HttpResponse(html)


class TransfertLineDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [ROLE_ADMIN]
    model = DetailsTransfertStock
    template_name = 'produits/transfert/transfert_confirm_delete.html'

    def get_transfert(self):
        return get_object_or_404(TransfertStock, pk=self.kwargs['transfert_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Supprimer un article du transfert"
        context['message'] = f"Voulez-vous supprimer l'article {self.get_object().article} du transfert ?"
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        context['transfert'] = self.get_transfert()
        return context

    def get_success_url(self):
        return reverse('transfert_details', kwargs={'pk': self.object.pk})

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        transfert = self.object.transfert

        self.object.delete()

        if request.headers.get('HX-Request') == 'true':
            details = DetailsTransfertStock.objects.filter(transfert=transfert)
            context = {
                'details_transfert': details,
                'transfert': transfert
            }
            return render(request, "produits/transfert/partials/_table.html", context)

        return redirect(self.get_success_url())


class TransfertSaveView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    model = TransfertStock
    template_name = 'produits/transfert/transfert_confirm_save.html'
    success_url = reverse_lazy('transferts_stock')

    def get_transfert(self):
        return get_object_or_404(TransfertStock, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Enregistrer un transfert'
        context['message'] = "Voulez-vous enregistrer et valider le transfert {} ?".format(self.get_transfert().numero)
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context

    def post(self, request, *args, **kwargs):
        transfert = self.get_transfert()
        TransfertService.valider_transfert(
            transfert=transfert,
        )
        return redirect(self.success_url)
