from django.urls import path, register_converter

from .converters import DateConverter, DateRangeConverter
from .views import (
    # Vues HTML
    RapportVenteView,
    RapportVenteDetailsView,
    RapportVenteDetailsFactureView,
    RapportResultatView,
    RapportArticleView,
    RapportCaisseView,
    RapportCommandeView,
    # Exports PDF
    export_rapport_ventes_pdf,
    export_rapport_resultat_pdf,
    export_rapport_articles_pdf,
    export_rapport_caisse_pdf,
    export_bon_commande_pdf,
    # Alias rétrocompatibilité
    export_rapport_pdf,
)

register_converter(DateConverter, 'simpledate')
register_converter(DateRangeConverter, 'date')

urlpatterns = [
    # ── Vues HTML ──────────────────────────────────────────────────────────
    path('rapport-ventes',
         RapportVenteView.as_view(),
         name='rapport_ventes'),
    path('rapport-ventes/<simpledate:date_facture>/details',
         RapportVenteDetailsView.as_view(),
         name='details_rapport_vente'),
    path('rapport-ventes/details/facture/<int:pk>/',
         RapportVenteDetailsFactureView.as_view(),
         name='rapport_vente_details_facture'),
    path('rapport-resultats',
         RapportResultatView.as_view(),
         name='rapport_resultats'),
    path('rapport-articles',
         RapportArticleView.as_view(),
         name='rapport_articles'),
    path('rapport-caisses',
         RapportCaisseView.as_view(),
         name='rapport_caisses'),
    path('rapport-commandes',
         RapportCommandeView.as_view(),
         name='rapport_commandes'),

    # ── Exports PDF ────────────────────────────────────────────────────────
    path('export-ventes-pdf/',
         export_rapport_ventes_pdf,
         name='export_rapport_ventes_pdf'),
    path('export-resultats-pdf/',
         export_rapport_resultat_pdf,
         name='export_rapport_resultat_pdf'),
    path('export-articles-pdf/',
         export_rapport_articles_pdf,
         name='export_rapport_articles_pdf'),
    path('export-caisses-pdf/',
         export_rapport_caisse_pdf,
         name='export_rapport_caisse_pdf'),
    path('export-bon-commande-pdf/',
         export_bon_commande_pdf,
         name='export_bon_commande_pdf'),

    # ── Rétrocompatibilité (ancienne URL utilisée dans rapport_vente.html) ─
    path('export_rapport_pdf/<date:date_range>/',
         export_rapport_pdf,
         name='export_rapport_pdf'),
]
