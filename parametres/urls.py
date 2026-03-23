from django.urls import path
from .views import (
    ParametresView, ParametresUpdateView,
    MagasinsView, MagasinCreateView, MagasinUpdateView,
    TauxEchangeListView, TauxEchangeCreateView, TauxEchangeUpdateView, TauxEchangeHistoryView,
    DevisesView, DeviseCreateView, DeviseUpdateView,
)

urlpatterns = [
    path('', ParametresView.as_view(), name='parametres'),
    path('update/<int:pk>', ParametresUpdateView.as_view(), name='parametres_update'),
    path('magasins/', MagasinsView.as_view(), name='magasins'),
    path('magasin/create', MagasinCreateView.as_view(), name='magasin_create'),
    path('magasin/<int:pk>/update', MagasinUpdateView.as_view(), name='magasin_update'),
    path('taux/', TauxEchangeListView.as_view(), name='taux_echange_list'),
    path('taux/create', TauxEchangeCreateView.as_view(), name='taux_echange_create'),
    path('taux/<int:pk>/update', TauxEchangeUpdateView.as_view(), name='taux_echange_update'),
    path('taux/<int:pk>/history', TauxEchangeHistoryView.as_view(), name='taux_echange_history'),
    path('devises/', DevisesView.as_view(), name='devises'),
    path('devise/create', DeviseCreateView.as_view(), name='devise_create'),
    path('devise/<int:pk>/update', DeviseUpdateView.as_view(), name='devise_update'),
]
