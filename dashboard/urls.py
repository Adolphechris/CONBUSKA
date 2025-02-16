from django.urls import path
from .views import DashboardBaseView

urlpatterns = [
    path('', DashboardBaseView.as_view(), name='index'),
]
