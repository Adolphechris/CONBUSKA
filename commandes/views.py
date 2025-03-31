from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from .models import Commande, DetailsCommande
from .forms import CommandeCreateForm, ArticleCommandeAddForm, ArticleCommandeUpdateForm


class CommandesView(LoginRequiredMixin, ListView):
    model = Commande
    context_object_name = 'liste_commandes'
    template_name = 'commandes/commandes.html'


class CommandeCreateView(LoginRequiredMixin, CreateView):
    model = Commande
    template_name = 'commandes/commande_form.html'
    form_class = CommandeCreateForm

    def form_valid(self, form, *args, **kwargs):
        commande = form.save(commit=False)
        commande.cree_par = self.request.user
        commande.save()
        return redirect('commande_details', pk=commande.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Creation commande'
        context['title_form'] = "Formulaire de creation d'une commande"
        context['cancel_url'] = reverse('commandes')
        return context

class CommandeUpdateView(LoginRequiredMixin, UpdateView):
    model = Commande
    template_name = 'commandes/commande_form.html'
    form_class = CommandeCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modification commande'
        context['title_form'] = 'Formulaire de modification de la commande #{}'.format(self.get_object().numero)
        context['cancel_url'] = reverse('commande_details', args=[self.get_object().pk])
        return context


class CommandeDeleteView(LoginRequiredMixin, DeleteView):
    model = Commande
    template_name = 'commandes/commande_confirm_delete.html'
    success_url = reverse_lazy('commandes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Annuler une commande'
        context['message'] = 'Voulez-vous annuler la commande {} ?'.format(self.get_object().numero)
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context

class CommandeSaveView(LoginRequiredMixin, TemplateView):
    model = Commande
    template_name = 'commandes/commande_confirm_save.html'
    success_url = reverse_lazy('commandes')

    def get_commande(self):
        return get_object_or_404(Commande, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Enregistrer une commande'
        context['message'] = 'Voulez-vous enregistrer la commande {} ?'.format(self.get_commande().numero)
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context

    def post(self, request, *args, **kwargs):
        commande = self.get_commande()
        commande.actif = False
        commande.save()
        return redirect('commandes')


class CommandeDetailView(LoginRequiredMixin, DetailView):
    model = Commande
    context_object_name = 'commande'
    template_name = 'commandes/commande_details.html'

    def get_details_commande(self):
        details_commande = DetailsCommande.objects.filter(commande=self.kwargs['pk'])
        return details_commande

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['details_commande'] = self.get_details_commande()
        return context


class ArticleCommandeAddView(LoginRequiredMixin, CreateView):
    model = DetailsCommande
    context_object_name = 'article_commande'
    template_name = 'commandes/add_article_form.html'
    form_class = ArticleCommandeAddForm

    def get_commande(self):
        return get_object_or_404(Commande, pk=self.kwargs['pk'])

    def form_valid(self, form, *args, **kwargs):
        detail_commande = form.save(commit=False)
        detail_commande.commande = self.get_commande()
        detail_commande.valid()
        return redirect('commande_details', pk=self.get_commande().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['commande'] = self.get_commande()
        return context


class ArticleCommandeUpdateView(LoginRequiredMixin, UpdateView):
    model = DetailsCommande
    template_name = 'commandes/edit_article_form.html'
    form_class = ArticleCommandeUpdateForm

    def get_commande(self):
        return get_object_or_404(Commande, pk=self.kwargs['commande_pk'])

    def get_form_kwargs(self):
        kwargs = super(ArticleCommandeUpdateView, self).get_form_kwargs()
        kwargs['article'] = self.object.article
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['commande'] = self.get_commande()
        return context
