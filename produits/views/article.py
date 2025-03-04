from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from produits.models import Article
from produits.forms import ArticleCreateForm


class ArticleView(LoginRequiredMixin, ListView):
    model = Article
    context_object_name = 'liste_articles'
    template_name = 'produits/article/articles.html'


class ArticleDetailsView(LoginRequiredMixin, DetailView):
    model = Article
    context_object_name = 'article'
    template_name = 'produits/article/article_details.html'


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    template_name = 'produits/article/article_create_form.html'
    form_class = ArticleCreateForm


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    template_name = 'produits/article/article_create_form.html'
    form_class = ArticleCreateForm


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = Article
    template_name = 'produits/article/article_confirm_delete.html'
    success_url = reverse_lazy('articles')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer un article'
        context['message'] = "Voulez-vous supprimer l'article {} ?".format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context