from django.urls import path
from .views import (FournisseursView, FournisseurCreateView, FournisseurDetailsView, FournisseurUpdateView,
                    FournisseurDeleteView)

urlpatterns = [
    path('', FournisseursView.as_view(), name='fournisseurs'),
    path('<int:pk>', FournisseurDetailsView.as_view(), name='fournisseur_details'),
    path('create', FournisseurCreateView.as_view(), name='fournisseur_create'),
    path('update/<int:pk>', FournisseurUpdateView.as_view(), name='fournisseur_update'),
    path('delete/<int:pk>', FournisseurDeleteView.as_view(), name='fournisseur_delete'),
]
