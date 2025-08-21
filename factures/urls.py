from django.urls import path
from .views import (FacturesView, FactureCreateView, FactureDetailView, get_update_form, ArticleFactureDeleteView)

urlpatterns = [
    path('', FacturesView.as_view(), name='factures'),
    path('facture/create', FactureCreateView.as_view(), name='facture_create'),
    path('facture/<int:pk>', FactureDetailView.as_view(), name='facture_details'),
    path('update_form_facture/<int:pk>/', get_update_form, name='get_form_update_facture'),
    path('facture/<int:facture_pk>/delete_article/<int:pk>', ArticleFactureDeleteView.as_view(),
         name='delete_article_facture')
]