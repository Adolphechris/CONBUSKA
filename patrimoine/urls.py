from django.urls import path
from .views import PatrimoineView

urlpatterns = [
    path('', PatrimoineView.as_view(), name='patrimoine'),
]