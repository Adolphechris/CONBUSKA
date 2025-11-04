from django.urls import path
from .views import (CreanciersView, CreancierCreateView, CreancierDetailsView, CreancierUpdateView, CreancierDeleteView,
                    DebiteursView, DebiteurCreateView, DebiteurDetailsView, DebiteurUpdateView, DebiteurDeleteView)

urlpatterns = [
    # ------- CREANCIERS ---------
    path('creanciers', CreanciersView.as_view(), name='creanciers'),
    path('creancier/<int:pk>', CreancierDetailsView.as_view(), name='creancier_details'),
    path('creancier/create', CreancierCreateView.as_view(), name='creancier_create'),
    path('creancier/update/<int:pk>', CreancierUpdateView.as_view(), name='creancier_update'),
    path('creancier/delete/<int:pk>', CreancierDeleteView.as_view(), name='creancier_delete'),
    # -------- DEBITEURS ----------
    path('debiteurs', DebiteursView.as_view(), name='debiteurs'),
    path('debiteur/<int:pk>', DebiteurDetailsView.as_view(), name='debiteur_details'),
    path('debiteur/create', DebiteurCreateView.as_view(), name='debiteur_create'),
    path('debiteur/update/<int:pk>', DebiteurUpdateView.as_view(), name='debiteur_update'),
    path('debiteur/delete/<int:pk>', DebiteurDeleteView.as_view(), name='debiteur_delete'),
]
