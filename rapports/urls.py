from django.urls import path, register_converter
from .views import (RapportVenteView, RapportVenteDetailsView, RapportVenteDetailsFactureView, RapportResultatView,
                    RapportArticleView)
from .converters import DateConverter

register_converter(DateConverter, 'date')

urlpatterns = [
    path('rapport-ventes', RapportVenteView.as_view(), name='rapport_ventes'),
    path('rapport-ventes/<date:date_facture>/details', RapportVenteDetailsView.as_view(), name='details_rapport_vente'),
    path('rapport-ventes/details/facture/<int:pk>/', RapportVenteDetailsFactureView.as_view(),
         name='rapport_vente_details_facture'),
    path('rapport-resultats', RapportResultatView.as_view(), name='rapport_resultats'),
    path('rapport-articles', RapportArticleView.as_view(), name='rapport_articles'),
]