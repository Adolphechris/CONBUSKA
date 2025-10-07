from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView


class PatrimoineView(LoginRequiredMixin, TemplateView):
    template_name = 'patrimoine/patrimoine.html'
