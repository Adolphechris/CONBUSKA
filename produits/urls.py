from django.urls import path
from .views import (CategorieView, CategorieCreateView, CategorieUpdateView, CategorieDetailsView, CategorieDeleteView,
                    UniteView, UniteDetailsView, UniteCreateView, UniteUpdateView, UniteDeleteView, ArticleView,
                    ArticleCreateView, ArticleDetailsView, ArticleUpdateView, ArticleDeleteView)

urlpatterns = [
    # ARTICLE URLS
    path('articles', ArticleView.as_view(), name='articles'),
    path('article/<int:pk>', ArticleDetailsView.as_view(), name='article_details'),
    path('article/create', ArticleCreateView.as_view(), name='article_create'),
    path('article/update/<int:pk>', ArticleUpdateView.as_view(), name='article_update'),
    path('article/delete/<int:pk>', ArticleDeleteView.as_view(), name='article_delete'),
    # CATEGORIE URLS
    path('categories', CategorieView.as_view(), name='categories'),
    path('categorie/<int:pk>', CategorieDetailsView.as_view(), name='categorie_details'),
    path('categorie/create', CategorieCreateView.as_view(), name='categorie_create'),
    path('categorie/update/<int:pk>', CategorieUpdateView.as_view(), name='categorie_update'),
    path('categorie/delete/<int:pk>', CategorieDeleteView.as_view(), name='categorie_delete'),
    # UNITE URLS
    path('unites', UniteView.as_view(), name='unites'),
    path('unite/<int:pk>', UniteDetailsView.as_view(), name='unite_details'),
    path('unite/create', UniteCreateView.as_view(), name='unite_create'),
    path('unite/update/<int:pk>', UniteUpdateView.as_view(), name='unite_update'),
    path('unite/delete/<int:pk>', UniteDeleteView.as_view(), name='unite_delete'),
]
