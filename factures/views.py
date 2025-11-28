import decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.views.generic import ListView, DetailView, TemplateView, RedirectView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404, render, HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.urls import reverse
from django.template.loader import render_to_string
from django.db.models import Min
from .models import Facture, DetailsFacture, Livreur, FactureClient
from .forms import ArticleFactureAddForm, ArticleFactureUpdateForm, InfosFactureForm, FactureClientForm
import random


class FacturesView(LoginRequiredMixin, ListView):
    model = Facture
    context_object_name = 'liste_factures'
    template_name = 'factures/factures.html'


class BaseFactureCreateMixin:
    """Mixin utilitaire pour créer une nouvelle facture avec un livreur aléatoire."""

    @staticmethod
    def get_random_livreur():
        min_livraison = Livreur.objects.aggregate(Min('livraison'))['livraison__min']
        livreurs = Livreur.objects.filter(livraison=min_livraison)
        random_livreur = random.choice(list(livreurs))
        random_livreur.livraison += 1
        random_livreur.save()
        return random_livreur

    def create_new_facture(self, user):
        """Crée une nouvelle facture avec un livreur choisi aléatoirement."""
        get_livreur = self.get_random_livreur()
        facture = Facture.objects.create(
            devise='FC',
            taux=2800,
            livreur=get_livreur,
            cree_par=user,
        )
        return facture


class FactureCreateView(LoginRequiredMixin, BaseFactureCreateMixin, RedirectView):
    """ Crée une facture brouillon non validée """
    permanent = False
    query_string = True
    pattern_name = "facture_details"

    def get_redirect_url(self, *args, **kwargs):
        facture = self.create_new_facture(self.request.user)
        return reverse('facture_details', kwargs={'pk': facture.pk})


class FactureValidateAndCreateView(LoginRequiredMixin, BaseFactureCreateMixin, View):
    """Valide la facture en cours et crée une nouvelle facture."""

    def get(self, request, *args, **kwargs):
        # On valide d'abord la facture actuelle
        facture = get_object_or_404(Facture, pk=kwargs.get("pk"))
        facture.valide = True
        facture.save(update_fields=['valide'])

        # On crée une nouvelle facture
        new_facture = self.create_new_facture(self.request.user)

        # Redirection vers la nouvelle facture
        response = HttpResponse()
        response["HX-Redirect"] = reverse('facture_details', kwargs={'pk': new_facture.pk})
        return response

@require_GET
def get_update_form(request, pk):
    instance = get_object_or_404(DetailsFacture, pk=pk)
    form = ArticleFactureUpdateForm(instance=instance)
    return render(request, "factures/partials/update_form.html",
                  {"update_form": form, "facture_pk": instance.facture.pk, "detail_facture_pk": pk})

class FactureDetailView(LoginRequiredMixin, DetailView):
    model = Facture
    context_object_name = 'facture'
    template_name = 'factures/facture_details.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        print("FACTURE CLIENT ", self.object.numero)
        context['info_form'] = InfosFactureForm(instance=self.object)
        context['add_form'] = ArticleFactureAddForm()
        context['update_form'] = ArticleFactureUpdateForm(
            instance=DetailsFacture.objects.filter(facture=self.kwargs['pk']).first()
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        print(request.headers, request.headers.get('HX-Request'))
        if request.headers.get('HX-Request') == 'true':
            form_type = request.POST.get('form_type')
            print(form_type)
            if form_type == 'add':
                form = ArticleFactureAddForm(request.POST)
                if form.is_valid():
                    detail_facture = form.save(commit=False)
                    detail_facture.facture = self.get_object()
                    detail_facture.article = form.cleaned_data['article']
                    detail_facture.add()

                    html = render_to_string("factures/partials/add_form_and_table.html", {
                        "add_form": ArticleFactureAddForm(),
                        "info_form": InfosFactureForm(),
                        "facture": self.get_object(),
                        "details_facture": self.get_details_facture()
                    }, request=request)

                    return HttpResponse(html)
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

            else:
                print(request.POST.get('id'), "##################################")
                instance = get_object_or_404(DetailsFacture, pk=request.POST.get('id'))
                form = ArticleFactureUpdateForm(request.POST, instance=instance)
                if form.is_valid():
                    detail_facture = form.save(commit=False)
                    detail_facture.update_facture()

                    html = render_to_string("factures/partials/add_form_and_table.html", {
                        "add_form": ArticleFactureAddForm(),
                        "facture": self.get_object(),
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


class FactureRemiseView(View):
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


class ArticleFactureDeleteView(LoginRequiredMixin, DeleteView):
    model = DetailsFacture
    template_name = 'factures/facture_article_confirm_delete.html'

    def get_facture(self):
        return get_object_or_404(Facture, pk=self.kwargs['facture_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Supprimer un article de la facture"
        context['message'] = f"Voulez-vous supprimer l'article {self.get_object().article} de la facture ?"
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        context['facture'] = self.get_facture()
        return context

    def get_success_url(self):
        return reverse('facture_details', kwargs={'pk': self.object.pk})

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        facture = self.object.facture

        # Mettre à jour le stock
        self.object.delete_facture()

        if request.headers.get('HX-Request') == 'true':
            details = DetailsFacture.objects.filter(facture=facture)
            context = {
                'details_facture': details,
                'facture': facture
            }
            return render(request, "factures/partials/lines_table.html", context)

        return redirect(self.get_success_url())


class FactureInfosUpdateView(LoginRequiredMixin, UpdateView):
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


class FactureClientCreateView(LoginRequiredMixin, CreateView):
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


class FactureClientUpdateView(LoginRequiredMixin, UpdateView):
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


class FactureClientDeleteView(LoginRequiredMixin, DeleteView):
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


class FactureShowDetailsView(LoginRequiredMixin, TemplateView):
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