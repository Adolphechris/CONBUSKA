from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .models import CustomUser
from .forms import UserEditProfileForm


class UserProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    context_object_name = 'user'
    template_name = 'users/user_profile.html'

    def get_object(self, queryset=None):
        return self.request.user


class UserProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'users/user_edit_profile_form.html'
    context_object_name = 'user'
    form_class = UserEditProfileForm
    success_url = reverse_lazy('user_profile')

    def get_object(self, queryset=None):
        return self.request.user


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy('user_profile')
    template_name = 'users/password_change_form.html'

    def form_valid(self, form):
        user = self.request.user
        if user.force_password_change:
            user.force_password_change = False
            user.save(update_fields=['force_password_change'])
        return super().form_valid(form)
