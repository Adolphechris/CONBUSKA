from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'module', 'action', 'description', 'ip_address')
    list_filter = ('module', 'action')
    search_fields = ('description', 'user__username')
    readonly_fields = ('created_at', 'user', 'action', 'module', 'description', 'ip_address')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
