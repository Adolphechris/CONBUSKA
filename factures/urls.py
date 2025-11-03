from django.urls import path
from .views import (FacturesView, FactureCreateView, FactureDetailView, get_update_form, FactureInfosUpdateView,
                    ArticleFactureDeleteView, FactureClientCreateView, FactureClientUpdateView, FactureClientDeleteView)

urlpatterns = [
    path('', FacturesView.as_view(), name='factures'),
    path('facture/create', FactureCreateView.as_view(), name='facture_create'),
    path('facture/<int:pk>', FactureDetailView.as_view(), name='facture_details'),
    path('update_form_facture/<int:pk>/', get_update_form, name='get_form_update_facture'),
    path('update_infos_facture/<int:pk>/', FactureInfosUpdateView.as_view(), name='facture_infos_update'),
    path('facture/<int:facture_pk>/delete_article/<int:pk>', ArticleFactureDeleteView.as_view(),
         name='delete_article_facture'),
    path('facture/<int:pk>/facture_client/create', FactureClientCreateView.as_view(), name='create_facture_client'),
    path('facture/<int:facture_pk>/facture_client/<int:pk>/update', FactureClientUpdateView.as_view(),
         name='update_facture_client'),
    path('facture/<int:pk>/facture_client/delete/', FactureClientDeleteView.as_view(), name='delete_facture_client'),
]