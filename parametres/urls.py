from django.urls import path
from .views import ParametresView, ParametresUpdateView, MagasinsView, MagasinCreateView, MagasinUpdateView

urlpatterns = [
    path('', ParametresView.as_view(), name='parametres'),
    path('update/<int:pk>', ParametresUpdateView.as_view(), name='parametres_update'),
    path('magasins/', MagasinsView.as_view(), name='magasins'),
    path('magasin/create', MagasinCreateView.as_view(), name='magasin_create'),
    path('magasin/<int:pk>/update', MagasinUpdateView.as_view(), name='magasin_update'),
]
