from django.urls import path
from .views import (
    ApprovisionnementsView,
    ApprovisionnementCreateView,
    ApprovisionnementDetailView,
    ApprovisionnementShowDetailsView,
    ApprovisionnementLineCreateView,
    ApprovisionnementLineUpdateView,
    ApprovisionnementUpdateView,
    ApprovisionnementDeleteView,
    ApprovisionnementSaveView,
    get_update_form,
    ArticleApprovisionnementDeleteView,
    BonApproPdfView,
)

urlpatterns = [
    path('', ApprovisionnementsView.as_view(), name='approvisionnements'),
    path('approvisionnement/create', ApprovisionnementCreateView.as_view(), name='approvisionnement_create'),
    path('approvisionnement/update/<int:pk>', ApprovisionnementUpdateView.as_view(), name='approvisionnement_update'),
    path('approvisionnement/delete/<int:pk>', ApprovisionnementDeleteView.as_view(), name='approvisionnement_delete'),
    path('approvisionnement/<int:pk>', ApprovisionnementDetailView.as_view(), name='approvisionnement_details'),
    path('approvisionnement/<int:pk>/show/details', ApprovisionnementShowDetailsView.as_view(),
         name='approvisionnement_show_details'),
    path('approvisionnement/<int:pk>/lines/add', ApprovisionnementLineCreateView.as_view(), name='approvisionnement_line_add'),
    path('approvisionnement/<int:pk>/lines/update', ApprovisionnementLineUpdateView.as_view(), name='approvisionnement_line_update'),
    path('approvisionnement/save/<int:pk>', ApprovisionnementSaveView.as_view(), name='approvisionnement_save'),
    path('update_form/<int:pk>/', get_update_form, name='get_form_update'),
    path('approvisionnement/<int:approvisionnement_pk>/delete_article/<int:pk>',
         ArticleApprovisionnementDeleteView.as_view(), name='delete_article_approvisionnement'),
    path('approvisionnement/<int:pk>/pdf', BonApproPdfView.as_view(), name='bon_appro_pdf'),
]
