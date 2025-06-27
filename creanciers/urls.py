from django.urls import path
from .views import (CreanciersView, CreancierCreateView, CreancierDetailsView, CreancierUpdateView, CreancierDeleteView)

urlpatterns = [
    path('', CreanciersView.as_view(), name='creanciers'),
    path('<int:pk>', CreancierDetailsView.as_view(), name='creancier_details'),
    path('create', CreancierCreateView.as_view(), name='creancier_create'),
    path('update/<int:pk>', CreancierUpdateView.as_view(), name='creancier_update'),
    path('delete/<int:pk>', CreancierDeleteView.as_view(), name='creancier_delete'),
]
