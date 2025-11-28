from django.urls import path, register_converter
from .views import (RapportVenteView, RapportVenteDetailsView, RapportVenteDetailsFactureView, RapportResultatView,
                    RapportArticleView, RapportCaisseView, export_rapport_pdf)
from .converters import DateConverter, DateRangeConverter

# register_converter(DateConverter, 'date')
register_converter(DateRangeConverter, 'date')

urlpatterns = [
    path('rapport-ventes', RapportVenteView.as_view(), name='rapport_ventes'),
    path('rapport-ventes/<date:date_facture>/details', RapportVenteDetailsView.as_view(), name='details_rapport_vente'),
    path('rapport-ventes/details/facture/<int:pk>/', RapportVenteDetailsFactureView.as_view(),
         name='rapport_vente_details_facture'),
    path('rapport-resultats', RapportResultatView.as_view(), name='rapport_resultats'),
    path('rapport-articles', RapportArticleView.as_view(), name='rapport_articles'),
    path('rapport-caisses', RapportCaisseView.as_view(), name='rapport_caisses'),
    path('export_rapport_pdf/<date:date_range>/', export_rapport_pdf, name='export_rapport_pdf'),
]