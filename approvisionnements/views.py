from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, View
from django.shortcuts import redirect, get_object_or_404, render, HttpResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from .models import Approvisionnement, DetailsApprovisionnement
from produits.models import Stock
from .forms import ApprovisionnementCreateForm, ArticleApprovisionnementAddForm, ArticleApprovisionnementUpdateForm
from .services import ApprovisionnementService


class ApprovisionnementsView(LoginRequiredMixin, ListView):
    model = Approvisionnement
    context_object_name = 'liste_approvisionnements'
    template_name = 'approvisionnements/approvisionnements.html'


class ApprovisionnementCreateView(LoginRequiredMixin, CreateView):
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


class ApprovisionnementUpdateView(LoginRequiredMixin, UpdateView):
    model = Approvisionnement
    template_name = 'approvisionnements/approvisionnement_form.html'
    form_class = ApprovisionnementCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modification approvisionnement'
        context['title_form'] = "Formulaire de modification de l'approvisionnement #{}".format(self.get_object().numero)
        context['cancel_url'] = reverse('approvisionnement_details', args=[self.get_object().pk])
        return context


class ApprovisionnementDeleteView(LoginRequiredMixin, DeleteView):
    model = Approvisionnement
    template_name = 'approvisionnements/approvisionnement_confirm_delete.html'
    success_url = reverse_lazy('approvisionnements')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Annuler un approvisionnement'
        context['message'] = "Voulez-vous annuler l'approvisionnement {} ?".format(self.get_object().numero)
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context

    def delete(self, request, *args, **kwargs):
        approvisionnement = self.get_object()
        ApprovisionnementService.supprimer(approvisionnement)
        return redirect(self.success_url)


class ApprovisionnementSaveView(LoginRequiredMixin, TemplateView):
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
        ApprovisionnementService.valider(
            approvisionnement=approvisionnement,
            user=request.user
        )
        return redirect(self.success_url)


@require_GET
def get_update_form(request, pk):
    instance = get_object_or_404(DetailsApprovisionnement, pk=pk)
    form = ArticleApprovisionnementUpdateForm(instance=instance)
    return render(request, "approvisionnements/partials/update_form.html",
                  {"update_form": form, "appro_pk": instance.approvisionnement.pk, "detail_appro_pk": pk})


class ApprovisionnementDetailView(LoginRequiredMixin, DetailView):
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
        return context

def is_htmx(request):
    return request.headers.get("HX-Request", "").lower() == "true"


class ApprovisionnementLineCreateView(LoginRequiredMixin, View):

    def post(self, request, pk):
        print(request.headers.get('X-Requested-With'), request.POST, request.POST.get('id'),
              request.POST.get('form_type'), request.headers.get("HX-Request"))
        test = is_htmx(request)
        print(test)
        if not is_htmx(request):
            print("******* ")
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
            detail.add()

        return self._render_table(request, approvisionnement)

    def _render_table(self, request, approvisionnement):
        html = render_to_string(
            "approvisionnements/partials/lines_table.html",
            {
                # "add_form": ArticleApprovisionnementAddForm(),
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


class ApprovisionnementLineUpdateView(LoginRequiredMixin, View):

    def post(self, request, pk):
        print(request.headers.get('X-Requested-With'), request.POST, request.POST.get('id'),
              request.POST.get('form_type'))
        if not request.headers.get("HX-Request"):
            return JsonResponse({"error": "HTMX required"}, status=400)

        detail = get_object_or_404(
            DetailsApprovisionnement,
            pk=request.POST.get('id')
        )

        approvisionnement = detail.approvisionnement

        form = ArticleApprovisionnementUpdateForm(
            request.POST,
            instance=detail
        )

        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)

        with transaction.atomic():
            detail = form.save(commit=False)
            detail.update_appro()

        return self._render_table(request, approvisionnement)

    def _render_table(self, request, approvisionnement):
        html = render_to_string(
            "approvisionnements/partials/lines_table.html",
            {
                # "add_form": ArticleApprovisionnementAddForm(),
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


"""
class ApprovisionnementDetailView(LoginRequiredMixin, DetailView):
    model = Approvisionnement
    context_object_name = 'approvisionnement'
    template_name = 'approvisionnements/approvisionnement_details.html'

    def get_details_approvisionnement(self):
        return DetailsApprovisionnement.objects.filter(approvisionnement=self.get_object())

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        # context['details_approvisionnement'] = self.get_details_approvisionnement()
        context['add_form'] = ArticleApprovisionnementAddForm()
        context['update_form'] = ArticleApprovisionnementUpdateForm(
            instance=DetailsApprovisionnement.objects.filter(approvisionnement=self.get_object())
        )  # ou autre instance logique
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        # print(request.headers.get('X-Requested-With'), request.POST, request.POST.get('id'), request.POST.get('form_type'))
        if request.headers.get('HX-Request'):
            form_type = request.POST.get('form_type')
            if form_type == 'add':
                form = ArticleApprovisionnementAddForm(request.POST)
                if form.is_valid():
                    detail_approvisionnement = form.save(commit=False)
                    detail_approvisionnement.approvisionnement = self.get_object()
                    detail_approvisionnement.article = form.cleaned_data['article']
                    detail_approvisionnement.fournisseur = form.cleaned_data['fournisseur']
                    detail_approvisionnement.add()

                    html = render_to_string("approvisionnements/partials/add_form_and_table.html", {
                        "add_form": ArticleApprovisionnementAddForm(),
                        "approvisionnement": self.get_object(),
                        "details_approvisionnement": self.get_details_approvisionnement()
                    }, request=request)

                    return HttpResponse(html)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

            else:
                instance = get_object_or_404(DetailsApprovisionnement, pk=request.POST.get('id'))
                form = ArticleApprovisionnementUpdateForm(request.POST, instance=instance)
                if form.is_valid():
                    detail_approvisionnement = form.save(commit=False)
                    detail_approvisionnement.update_appro()

                    html = render_to_string("approvisionnements/partials/add_form_and_table.html", {
                        "add_form": ArticleApprovisionnementAddForm(),
                        "approvisionnement": self.get_object(),
                        "details_approvisionnement": self.get_details_approvisionnement()
                    }, request=request)

                    return HttpResponse(html)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        return JsonResponse({'error': 'Invalid request'}, status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['details_approvisionnement'] = self.get_details_approvisionnement()
        return context
"""


class ArticleApprovisionnementDeleteView(LoginRequiredMixin, DeleteView):
    model = DetailsApprovisionnement
    template_name = 'approvisionnements/approvisionnement_confirm_delete.html'

    def get_approvisionnement(self):
        return get_object_or_404(Approvisionnement, pk=self.kwargs['approvisionnement_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Supprimer un article de l'approvisionnement"
        context['message'] = f"Voulez-vous supprimer l'article {self.get_object().article} de l'approvisionnement ?"
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        context['approvisionnement'] = self.get_approvisionnement()
        return context

    def get_success_url(self):
        return reverse('approvisionnement_details', kwargs={'pk': self.object.pk})

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        appro = self.object.approvisionnement

        # Supprimer ou mettre à jour le stock
        stock = Stock.objects.get(
            magasin=appro.magasin,
            article=self.object.article,
            date_peremption=self.object.date_peremption
        )
        stock.qte -= self.object.qte
        if stock.qte <= 0:
            stock.delete()
        else:
            stock.save()

        self.object.delete()

        if request.headers.get('HX-Request') == 'true':
            details = DetailsApprovisionnement.objects.filter(approvisionnement=appro)
            context = {
                'details_approvisionnement': details,
                'approvisionnement': appro
            }
            return render(request, "approvisionnements/partials/lines_table.html", context)

        return redirect(self.get_success_url())
