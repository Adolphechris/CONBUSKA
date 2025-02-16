from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView, RedirectView, View
from django.urls import reverse_lazy
import json
from operator import itemgetter
from itertools import groupby


class DashboardAdminView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'


class DashboardBaseView(LoginRequiredMixin, View):
    login_url = '/login/'
    admin_view = staticmethod(DashboardAdminView.as_view())

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        else:
            if str(self.request.user.username) != 'DOE':
                return self.admin_view(request, *args, **kwargs)

            else:
                pass
