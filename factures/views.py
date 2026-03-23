import datetime
import decimal
from django.core.exceptions import ValidationError
from users.permissions import RoleRequiredMixin, ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN, user_has_role
from django.db import transaction
from django.views.generic import ListView, DetailView, TemplateView, RedirectView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404, render, HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.template.loader import render_to_string
from django.db.models import Min, F
from django.core.exceptions import PermissionDenied
from .models import Facture, DetailsFacture, Livreur, FactureClient
from .forms import ArticleFactureAddForm, ArticleFactureUpdateForm, InfosFactureForm, FactureClientForm
from .services import FactureService
from .exceptions import FactureError
import random
from parametres.models import get_taux_usd_cdf
from utils.pdf_generator import DocumentGenerator


class FacturesView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    model = Facture
    context_object_name = 'liste_factures'
    template_name = 'factures/factures.html'
    ordering = ['-numero']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = user_has_role(self.request.user, ROLE_ADMIN)
        return context


class BaseFactureCreateMixin:
    """Mixin utilitaire pour créer une nouvelle facture avec un livreur aléatoire."""

    @staticmethod
    @transaction.atomic
    def get_random_livreur():
        min_livraison = Livreur.objects.aggregate(Min('livraison'))['livraison__min']
        livreurs = list(Livreur.objects.select_for_update().filter(livraison=min_livraison))
        random_livreur = random.choice(livreurs)
        Livreur.objects.filter(pk=random_livreur.pk).update(livraison=F('livraison') + 1)
        return random_livreur

    def get_taux(self):
        return get_taux_usd_cdf()

    def create_new_facture(self, user):
        """Crée une nouvelle facture avec un livreur choisi aléatoirement.
        Purge d'abord les brouillons vides de cet utilisateur créés avant aujourd'hui."""
        today = datetime.date.today()
        Facture.objects.filter(
            cree_par=user,
            valide=False,
            date_creation__date__lt=today,
        ).exclude(
            pk__in=DetailsFacture.objects.values('facture_id')
        ).delete()

        get_livreur = self.get_random_livreur()
        facture = Facture.objects.create(
            devise='FC',
            taux=self.get_taux(),
            livreur=get_livreur,
            cree_par=user,
        )
        return facture


class FactureCreateView(RoleRequiredMixin, BaseFactureCreateMixin, RedirectView):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    """ Crée une facture brouillon non validée """
    permanent = False
    query_string = True
    pattern_name = "facture_details"

    def get_redirect_url(self, *args, **kwargs):
        facture = self.create_new_facture(self.request.user)
        return reverse('facture_details', kwargs={'pk': facture.pk})


class FactureValidateAndCreateView(RoleRequiredMixin, BaseFactureCreateMixin, View):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    """Valide la facture en cours et crée une nouvelle facture."""

    def post(self, request, *args, **kwargs):
        facture = get_object_or_404(Facture, pk=kwargs.get("pk"))

        date_facture = None
        date_str = request.POST.get('date_facture')
        if date_str:
            try:
                date_facture = datetime.date.fromisoformat(date_str)
            except ValueError:
                pass

        try:
            FactureService.valider(facture=facture, user=request.user, date_facture=date_facture)
        except (ValidationError, FactureError) as e:
            return HttpResponse(str(e), status=400)

        new_facture = self.create_new_facture(self.request.user)

        response = HttpResponse()
        response["HX-Redirect"] = reverse('facture_details', kwargs={'pk': new_facture.pk})
        return response


class FactureRemiseView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    """Met à jour la remise d'une facture."""

    def post(self, request, pk):
        facture = get_object_or_404(Facture, pk=pk)
        remise = request.POST.get('remise', 0)

        try:
            remise = float(remise)
        except ValueError:
            remise = 0

        # Met à jour la remise
        facture.remise = decimal.Decimal(remise)
        facture.save(update_fields=['remise'])

        # Renvoie le fragment HTML mis à jour
        return render(request, "factures/partials/facture_summary_partial.html", {"facture": facture})


@login_required
@require_GET
def get_update_form(request, pk):
    if not user_has_role(request.user, ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN):
        raise PermissionDenied
    instance = get_object_or_404(DetailsFacture, pk=pk)
    form = ArticleFactureUpdateForm(instance=instance)
    return render(request, "factures/partials/update_form.html", {
        "update_form": form,
        "facture_pk": instance.facture.pk,
        "detail_facture_pk": pk,
        "article_nom": instance.article.designation,
    })

class FactureDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    model = Facture
    context_object_name = 'facture'
    template_name = 'factures/facture_details.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['info_form'] = InfosFactureForm(instance=self.object)
        context['add_form'] = ArticleFactureAddForm()
        context['update_form'] = ArticleFactureUpdateForm(
            instance=DetailsFacture.objects.filter(facture=self.kwargs['pk']).first()
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        facture = self.get_object()

        if request.headers.get('HX-Request') == 'true':
            form_type = request.POST.get('form_type')

            if form_type == 'add':
                form = ArticleFactureAddForm(request.POST)
                if form.is_valid():
                    try:
                        FactureService.ajouter_article_facture(
                            facture=facture,
                            article=form.cleaned_data['article'],
                            qte=form.cleaned_data['qte']
                        )
                    except ValidationError as e:
                        return JsonResponse({'success': False, 'errors': {'stock': e.messages}}, status=400)

                    html = render_to_string("factures/partials/add_form_and_table.html", {
                        "add_form": ArticleFactureAddForm(),
                        "info_form": InfosFactureForm(),
                        "facture": facture,
                        "details_facture": self.get_details_facture()
                    }, request=request)

                    return HttpResponse(html)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

            else:
                instance = get_object_or_404(DetailsFacture, pk=request.POST.get('id'))
                form = ArticleFactureUpdateForm(request.POST, instance=instance)
                if form.is_valid():
                    try:
                        FactureService.modifier_article_facture(
                            facture=facture,
                            article=instance.article,  # article verrouillé — jamais modifiable
                            qte_nouvelle=form.cleaned_data['qte']
                        )
                    except ValidationError as e:
                        return JsonResponse({'success': False, 'errors': {'stock': e.messages}}, status=400)

                    html = render_to_string("factures/partials/add_form_and_table.html", {
                        "add_form": ArticleFactureAddForm(),
                        "facture": facture,
                        "info_form": InfosFactureForm(),
                        "details_facture": self.get_details_facture()
                    }, request=request)

                    return HttpResponse(html)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        return JsonResponse({'error': 'Invalid request'}, status=400)

    def get_details_facture(self):
        details_facture = DetailsFacture.objects.filter(facture=self.kwargs['pk'])
        return details_facture

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['details_facture'] = self.get_details_facture()
        return context


class ArticleFactureDeleteView(RoleRequiredMixin, View):

    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    def get(self, request, facture_pk, pk):
        facture = get_object_or_404(Facture, pk=facture_pk)
        detail = get_object_or_404(DetailsFacture, pk=pk, facture=facture)

        context = {
            "title": "Supprimer un article de la facture",
            "message": f"Voulez-vous supprimer l'article {detail.article.designation} de la facture ?",
            "submit_icon": "fa fa-check",
            "submit_label": "Valider",
            "facture": facture,
            "detail": detail,
        }

        return render(
            request,
            "factures/facture_article_confirm_delete.html",
            context
        )

    def post(self, request, facture_pk, pk):
        facture = get_object_or_404(Facture, pk=facture_pk)
        detail = get_object_or_404(DetailsFacture, pk=pk, facture=facture)

        FactureService.supprimer_article_facture(
            facture=facture,
            article=detail.article,
        )

        if request.headers.get("HX-Request"):
            details = DetailsFacture.objects.filter(facture=facture)

            context = {
                "details_facture": details,
                "facture": facture,
                # "add_form": ArticleFactureAddForm(),
                # "info_form": InfosFactureForm(),
            }

            html = render_to_string('factures/partials/lines_table.html', context)

            response = HttpResponse(html)
            response["HX-Trigger"] = "closeMainModal"
            return response

        return redirect("facture_details", pk=facture.pk)


class FactureInfosUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    model = Facture
    form_class = InfosFactureForm
    template_name = 'factures/partials/info_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Facture, pk=self.kwargs['pk'])

    def form_valid(self, form):
        self.object = form.save()

        if self.request.headers.get("HX-Request"):
            context = {
                'info_form': self.get_form(),
                'facture': self.object
            }
            html = render_to_string(self.template_name, context, request=self.request)
            return JsonResponse({'success': True, 'html': html})
        return redirect('facture_details', pk=self.object.pk)

    def form_invalid(self, form):
        context = {
            'info_form': form,
            'facture': self.get_object()
        }
        html = render_to_string(self.template_name, context, request=self.request)
        return JsonResponse({'success': False, 'html': html})


class FactureClientCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    model = FactureClient
    template_name = 'factures/partials/facture_client_form.html'
    form_class = FactureClientForm

    def get_facture(self):
        return get_object_or_404(Facture, pk=self.kwargs['pk'])


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['facture'] = self.get_facture()
        return context


    def form_valid(self, form):
        facture = self.get_facture()
        facture.client_comptoir = None
        facture.save(update_fields=['client_comptoir'])

        facture_client = form.save(commit=False)
        facture_client.facture = facture
        facture_client.save()

        context = {
            'facture': self.get_facture(),
        }

        html = render_to_string('factures/partials/facture_client_partial.html', context)

        response = HttpResponse(html)
        response["HX-Trigger"] = "closeModalClient"
        return response

    def form_invalid(self, form):
        # S'assure que le formulaire est affiché dans la modale même si invalide
        return render(self.request, self.template_name, {
            'form': form,
            'facture': self.get_facture()
        })


class FactureClientUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    model = FactureClient
    template_name = 'factures/partials/facture_client_form.html'
    form_class = FactureClientForm

    def get_facture(self):
        return get_object_or_404(Facture, pk=self.kwargs['facture_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['facture'] = self.get_facture()
        return context

    def form_valid(self, form):
        facture_client = form.save(commit=False)
        facture_client.save()

        context = {
            'facture': self.get_facture(),
        }

        html = render_to_string('factures/partials/facture_client_partial.html', context)

        response = HttpResponse(html)
        response["HX-Trigger"] = "closeModalClient"
        return response

    def form_invalid(self, form):
        # S'assure que le formulaire est affiché dans la modale même si invalide
        return render(self.request, self.template_name, {
            'form': form,
            'facture': self.get_facture()
        })


class FactureClientDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    model = FactureClient

    def delete(self, request, *args, **kwargs):
        facture_client = self.get_object()
        facture = facture_client.facture
        facture_client.delete()

        # Retour à l’état initial (info_form.html)
        info_form = InfosFactureForm(instance=facture)
        context = {'facture': facture, 'info_form': info_form}
        html = render_to_string('factures/partials/info_form.html', context)
        return HttpResponse(html)


class FactureShowDetailsView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    template_name = 'factures/facture_show_details.html'

    def get_facture(self):
        return get_object_or_404(Facture, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        facture = self.get_facture()
        details_facture = DetailsFacture.objects.filter(facture=facture.pk)
        context['facture'] = facture
        context['details_facture'] = details_facture
        return context


class FactureDeleteView(RoleRequiredMixin, View):

    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]
    def get(self, request, pk):
        facture = get_object_or_404(Facture, pk=pk)

        context = {
            "title": "Suppression facture",
            "message": f"Voulez-vous supprimer la facture {facture.numero} ?",
            "submit_icon": "fa fa-check",
            "submit_label": "Valider",
            "facture": facture,
        }

        return render(
            request,
            "factures/facture_confirm_delete.html",
            context
        )

    def post(self, request, pk):
        facture = get_object_or_404(Facture, pk=pk)

        FactureService.supprimer(facture=facture)

        if request.headers.get("HX-Request"):
            # Redirection vers la liste des factures
            response = HttpResponse()
            response["HX-Redirect"] = reverse('factures')
            return response

        return redirect("factures")


class PurgeEmptyDraftsView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]

    def post(self, request):
        Facture.objects.filter(
            valide=False,
        ).exclude(
            pk__in=DetailsFacture.objects.values('facture_id')
        ).delete()

        if request.headers.get("HX-Request"):
            response = HttpResponse()
            response["HX-Redirect"] = reverse('factures')
            return response
        return redirect('factures')


class FacturePdfView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN, ROLE_FACTURIER, ROLE_GERANT_MAGASIN]

    def get(self, request, pk):
        facture = get_object_or_404(Facture, pk=pk)
        details = DetailsFacture.objects.filter(facture=facture).select_related('article')
        gen = DocumentGenerator(
            filename=f'facture_{facture.numero}.pdf',
            title=f'Facture N° {facture.numero}',
        )
        return gen.generate_facture(facture=facture, details=details)