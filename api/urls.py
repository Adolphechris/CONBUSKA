from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategorieViewSet, ArticleViewSet, CommandeViewSet

router = DefaultRouter()
router.register(r'categories', CategorieViewSet, basename='categorie')
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'commandes', CommandeViewSet, basename='commande')

urlpatterns = [
    path('', include(router.urls)),
]