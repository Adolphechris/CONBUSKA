from django.urls import path
from .views import (ApprovisionnementsView, ApprovisionnementCreateView, ApprovisionnementDetailView,
                    ApprovisionnementUpdateView, ApprovisionnementDeleteView, ApprovisionnementSaveView,
                    ArticleApprovisionnementAddView, ArticleApprovisionnementUpdateView, get_update_form)

urlpatterns = [
    path('', ApprovisionnementsView.as_view(), name='approvisionnements'),
    path('approvisionnement/<int:pk>', ApprovisionnementDetailView.as_view(), name='approvisionnement_details'),
    path('approvisionnement/create', ApprovisionnementCreateView.as_view(), name='approvisionnement_create'),
    path('approvisionnement/update/<int:pk>', ApprovisionnementUpdateView.as_view(), name='approvisionnement_update'),
    path('approvisionnement/delete/<int:pk>', ApprovisionnementDeleteView.as_view(), name='approvisionnement_delete'),
    path('approvisionnement/save/<int:pk>', ApprovisionnementSaveView.as_view(), name='approvisionnement_save'),
    path('approvisionnement/<int:pk>/add_article', ArticleApprovisionnementAddView.as_view(),
         name='add_article_approvisionnement'),
    path('approvisionnement/<int:approvisionnement_pk>/update_article/<int:pk>',
         ArticleApprovisionnementUpdateView.as_view(), name='update_article_approvisionnement'),
    path('update_form/<int:pk>/', get_update_form, name='get_form_update')
]
