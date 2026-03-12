from django.views.generic import ListView

from .filters import ActivityLogFilter
from .models import ActivityLog
from users.permissions import RoleRequiredMixin, ROLE_ADMIN


class LogsView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = ActivityLog
    template_name = 'activity_logs/logs.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        qs = ActivityLog.objects.select_related('user').all()
        self.filter = ActivityLogFilter(self.request.GET, queryset=qs)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter'] = self.filter
        ctx['total'] = self.filter.qs.count()
        return ctx
