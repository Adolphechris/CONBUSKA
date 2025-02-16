from django.urls import path
from .views import ParametresView, ParametresUpdateView

urlpatterns = [
    path('', ParametresView.as_view(), name='parametres'),
    path('update/<int:pk>', ParametresUpdateView.as_view(), name='parametres_update'),
]