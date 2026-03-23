from django.urls import path
from .views import DashboardBaseView, TopArticlesView

urlpatterns = [
    path('', DashboardBaseView.as_view(), name='index'),
    path('top-articles/', TopArticlesView.as_view(), name='top_articles'),
]
