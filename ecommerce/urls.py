from django.urls import path
from django.contrib import admin
from .views import (
    ArticleEcommerceListView,
    EcommerceDashboardView,
    ForceSyncView,
    SyncLogsView,
    SyncQueueView,
    TogglePublicationView,
    sync_dashboard_view,
)

urlpatterns = [
    path('', EcommerceDashboardView.as_view(), name='ecommerce_dashboard'),
    path('articles', ArticleEcommerceListView.as_view(), name='ecommerce_articles'),
    path('article/<int:pk>/toggle', TogglePublicationView.as_view(), name='ecommerce_toggle'),
    path('sync/logs', SyncLogsView.as_view(), name='ecommerce_sync_logs'),
    path('sync/queue', SyncQueueView.as_view(), name='ecommerce_sync_queue'),
    path('sync/force', ForceSyncView.as_view(), name='ecommerce_sync_force'),
    path('admin/sync-dashboard/', admin.site.admin_view(sync_dashboard_view), name='sync_dashboard'),
]
