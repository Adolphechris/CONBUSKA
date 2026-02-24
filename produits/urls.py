from django.urls import path
from .views import (CategorieView, CategorieCreateView, CategorieUpdateView, CategorieDetailsView, CategorieDeleteView,
                    UniteView, UniteDetailsView, UniteCreateView, UniteUpdateView, UniteDeleteView, ArticleView,
                    ArticleCreateView, ArticleDetailsView, ArticleUpdateView, ArticleDeleteView,
                    ArticleActivateOrDeactivateView, FicheStockView, HistoriqueTransfertStockView, TransfertCreateView,
                    TransfertDetailView, TransfertLineCreateView, TransfertLineUpdateView, TransfertLineDeleteView,
                    TransfertSaveView, get_form_update_transfert)

urlpatterns = [
    # ARTICLE URLS
    path('articles', ArticleView.as_view(), name='articles'),
    path('article/<int:pk>', ArticleDetailsView.as_view(), name='article_details'),
    path('article/create', ArticleCreateView.as_view(), name='article_create'),
    path('article/update/<int:pk>', ArticleUpdateView.as_view(), name='article_update'),
    path('article/delete/<int:pk>', ArticleDeleteView.as_view(), name='article_delete'),
    path('article/<int:pk>/activate_deactivate', ArticleActivateOrDeactivateView.as_view(), name='activate_or_deactivate'),
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
    # FICHE STOCK URLS
    path('fiche_stock', FicheStockView.as_view(), name='fiche_stock'),
    # TRANSFERTS STOCK URLS
    path('transferts', HistoriqueTransfertStockView.as_view(), name='transferts_stock'),
    path('transfert/<int:pk>', TransfertDetailView.as_view(), name='transfert_details'),
    path('transfert/create', TransfertCreateView.as_view(), name='transfert_create'),
    path('transfert/<int:pk>/line/add', TransfertLineCreateView.as_view(), name='transfert_line_add'),
    path('transfert/<int:pk>/line/update', TransfertLineUpdateView.as_view(), name='transfert_line_update'),
    path('transfert/update_form/<int:pk>/', get_form_update_transfert, name='get_form_update_transfert'),
    path('transfert/<int:transfert_pk>/delete_article/<int:pk>', TransfertLineDeleteView.as_view(),
         name='transfert_line_delete'),
    path('transfert/<int:pk>/save', TransfertSaveView.as_view(), name='transfert_save'),
]
