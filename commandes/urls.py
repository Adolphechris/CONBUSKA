from django.urls import path
from .views import (CommandesView, CommandeCreateView, CommandeDetailView, CommandeUpdateView, CommandeDeleteView,
                    CommandeSaveView, ArticleCommandeAddView, ArticleCommandeUpdateView)

urlpatterns = [
    path('', CommandesView.as_view(), name='commandes'),
    path('commande/<int:pk>', CommandeDetailView.as_view(), name='commande_details'),
    path('commande/create', CommandeCreateView.as_view(), name='commande_create'),
    path('commande/update/<int:pk>', CommandeUpdateView.as_view(), name='commande_update'),
    path('commande/delete/<int:pk>', CommandeDeleteView.as_view(), name='commande_delete'),
    path('commande/save/<int:pk>', CommandeSaveView.as_view(), name='commande_save'),
    path('commande/<int:pk>/add_article', ArticleCommandeAddView.as_view(), name='add_article_commande'),
    path('commande/<int:commande_pk>/update_article/<int:pk>', ArticleCommandeUpdateView.as_view(),
         name='update_article_commande'),
]
