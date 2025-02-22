from django.urls import path
from .views import (CategorieView, CategorieCreateView, CategorieUpdateView, CategorieDetailsView, CategorieDeleteView)

urlpatterns = [
    # CATEGORIES URLS
    path('categories', CategorieView.as_view(), name='categories'),
    path('<int:pk>', CategorieDetailsView.as_view(), name='categorie_details'),
    path('create', CategorieCreateView.as_view(), name='categorie_create'),
    path('update/<int:pk>', CategorieUpdateView.as_view(), name='categorie_update'),
    path('delete/<int:pk>', CategorieDeleteView.as_view(), name='categorie_delete'),
]
