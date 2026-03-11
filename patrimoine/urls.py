from django.urls import path
from .views import (PatrimoineView, JournalTransactionsView, CalendrierFinancierView, StatistiquesFinancieresView,
                    ResultatsView, SuiviCapitauxView, PatrimoineExportPDFView, ValiderFRView)

urlpatterns = [
    path('', PatrimoineView.as_view(), name='patrimoine'),
    path("journal/", JournalTransactionsView.as_view(), name="patrimoine_journal"),
    path("calendrier/", CalendrierFinancierView.as_view(), name="patrimoine_calendrier"),
    path("statistiques/", StatistiquesFinancieresView.as_view(), name="patrimoine_statistiques"),
    path("resultats/", ResultatsView.as_view(), name="patrimoine_resultats"),
    path("capitaux/", SuiviCapitauxView.as_view(), name="patrimoine_capitaux"),
    path("capitaux/<int:pk>/valider/", ValiderFRView.as_view(), name="patrimoine_valider_fr"),
    path("export/pdf/", PatrimoineExportPDFView.as_view(), name="patrimoine_export_pdf"),
]