from django.urls import path
from .views import (CaisseView, CaissesView, OuvertureCaisseView, HistoriqueCaisseView, MouvementCaisseDeleteView,
                    get_update_caisse_form, rubrique_champ_view, ClotureCaisseView)

urlpatterns = [
    path('caisses', CaissesView.as_view(), name='caisses'),
    path('<int:pk>/historique', HistoriqueCaisseView.as_view(), name='historique_caisse'),
    path('ouverture', OuvertureCaisseView.as_view(), name='ouverture_caisse'),
    path('<int:pk>/ouverture', OuvertureCaisseView.as_view(), name='ouverture_caisse'),
    path('<int:pk>', CaisseView.as_view(), name='caisse_details'),
    path('update_caisse_form/<int:pk>/', get_update_caisse_form, name='get_form_caisse_update'),
    path('<int:caisse_pk>/delete_mouvement/<int:pk>/', MouvementCaisseDeleteView.as_view(), name='delete_mouvement_caisse'),
    path('<int:caisse_pk>/rubrique_champ/', rubrique_champ_view, name='rubrique_champ'),
    path('<int:pk>/cloture', ClotureCaisseView.as_view(), name='cloture_caisse'),
]