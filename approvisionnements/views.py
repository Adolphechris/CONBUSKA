from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404, render
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.template.loader import render_to_string
from .models import Approvisionnement, DetailsApprovisionnement
from .forms import ApprovisionnementCreateForm, ArticleApprovisionnementAddForm, ArticleApprovisionnementUpdateForm


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
        approvisionnement.actif = False
        approvisionnement.save()
        return redirect('approvisionnements')


@require_GET
def get_update_form(request, pk):
    instance = get_object_or_404(DetailsApprovisionnement, pk=pk)
    print(instance.article, '############# ')
    form = ArticleApprovisionnementUpdateForm(instance=instance)
    return render(request, "approvisionnements/update_form.html", {"update_form": form, 'form_id': pk})


class ApprovisionnementDetailView(LoginRequiredMixin, DetailView):
    model = Approvisionnement
    context_object_name = 'approvisionnement'
    template_name = 'approvisionnements/approvisionnement_details.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['add_form'] = ArticleApprovisionnementAddForm()
        context['update_form'] = ArticleApprovisionnementUpdateForm(
            instance=DetailsApprovisionnement.objects.filter(approvisionnement=self.kwargs['pk']).first()
        )  # ou autre instance logique
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form_type = request.POST.get('form_type')
            if form_type == 'add':
                form = ArticleApprovisionnementAddForm(request.POST)
                if form.is_valid():
                    print("********** HTMX POST",)
                    """
                    detail_approvisionnement = form.save(commit=False)
                    detail_approvisionnement.approvisionnement = self.get_object()
                    detail_approvisionnement.article = form.cleaned_data['article']
                    detail_approvisionnement.fournisseur = form.cleaned_data['fournisseur']
                    detail_approvisionnement.add_details()
                    """
                    return JsonResponse({'success': True})
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

            else:
                instance = get_object_or_404(DetailsApprovisionnement, pk=request.POST.get('id'))  # ou autre logique d'instance
                form = ArticleApprovisionnementUpdateForm(request.POST, instance=instance)
                if form.is_valid():
                    form.save()
                    return JsonResponse({'success': True})
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        return JsonResponse({'error': 'Invalid request'}, status=400)

    def get_details_approvisionnement(self):
        details_approvisionnement = DetailsApprovisionnement.objects.filter(approvisionnement=self.kwargs['pk'])
        return details_approvisionnement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['details_approvisionnement'] = self.get_details_approvisionnement()
        return context


class ArticleApprovisionnementAddView(LoginRequiredMixin, CreateView):
    model = DetailsApprovisionnement
    context_object_name = 'article_approvisionnement'
    template_name = 'approvisionnements/add_article_form.html'
    form_class = ArticleApprovisionnementAddForm

    def get_approvisionnement(self):
        return get_object_or_404(Approvisionnement, pk=self.kwargs['pk'])

    def form_valid(self, form, *args, **kwargs):
        detail_approvisionnement = form.save(commit=False)
        detail_approvisionnement.approvisionnement = self.get_approvisionnement()
        detail_approvisionnement.valid()
        return redirect('approvisionnement_details', pk=self.get_approvisionnement().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['approvisionnement'] = self.get_approvisionnement()
        return context


class ArticleApprovisionnementUpdateView(LoginRequiredMixin, UpdateView):
    model = DetailsApprovisionnement
    template_name = 'approvisionnements/edit_article_form.html'
    form_class = ArticleApprovisionnementUpdateForm

    def get_approvisionnement(self):
        return get_object_or_404(Approvisionnement, pk=self.kwargs['approvisionnement_pk'])

    def get_form_kwargs(self):
        kwargs = super(ArticleApprovisionnementUpdateView, self).get_form_kwargs()
        kwargs['article'] = self.object.article
        return kwargs

    def form_valid(self, form, *args, **kwargs):
        print(self.get_object().qte, self.get_object().date_peremption)
        detail_approvisionnement = form.save(commit=False)
        detail_approvisionnement.update_details(self.get_object())
        return redirect('approvisionnement_details', pk=self.get_approvisionnement().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['approvisionnement'] = self.get_approvisionnement()
        return context
