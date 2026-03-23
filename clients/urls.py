from django.urls import path
from .views import (ClientsView, ClientCreateView, ClientDetailsView, ClientUpdateView, ClientDeleteView,
                    ClientRelevePdfView)

urlpatterns = [
    path('', ClientsView.as_view(), name='clients'),
    path('<int:pk>', ClientDetailsView.as_view(), name='client_details'),
    path('create', ClientCreateView.as_view(), name='client_create'),
    path('update/<int:pk>', ClientUpdateView.as_view(), name='client_update'),
    path('delete/<int:pk>', ClientDeleteView.as_view(), name='client_delete'),
    path('<int:pk>/releve', ClientRelevePdfView.as_view(), name='client_releve_pdf'),
]
