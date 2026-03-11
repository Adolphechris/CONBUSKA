from users.permissions import RoleRequiredMixin, ROLE_ADMIN
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from users.models import CustomUser
from .forms import UserCreateForm, UserEditForm, UserPasswordForm


class UsersView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN]
    model = CustomUser
    context_object_name = 'users'
    template_name = 'users/users.html'


class UserDetailsView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = CustomUser
    context_object_name = 'user_details'
    template_name = 'users/user_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class UserCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = CustomUser
    template_name = 'users/user_create_form.html'
    context_object_name = 'user'
    form_class = UserCreateForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_unusable_password()
        user.save()

        return super(UserCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('user_set_password', kwargs={'pk': self.object.pk})


class UserEditView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = CustomUser
    template_name = 'users/user_edit_form.html'
    context_object_name = 'user_edit'
    form_class = UserEditForm
    success_url = reverse_lazy('users')

    def form_valid(self, form):
        user = form.save()

        return super(UserEditView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(UserEditView, self).get_form_kwargs()
        kwargs['user'] = self.object
        return kwargs


class UserSetPasswordView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = CustomUser
    template_name = 'users/user_set_password_form.html'
    context_object_name = 'user_password'
    form_class = UserPasswordForm
    success_url = reverse_lazy('users')

    def get_form_kwargs(self):
        kwargs = super(UserSetPasswordView, self).get_form_kwargs()
        kwargs['user'] = self.object
        return kwargs

    def form_valid(self, form):
        """After admin sets a password, clear force_password_change so the user
        is prompted to set their own on first login."""
        response = super().form_valid(form)
        user = self.object
        user.force_password_change = True
        user.save(update_fields=['force_password_change'])
        return response


class UserToggleActiveView(RoleRequiredMixin, View):
    """Activate or deactivate a user account."""
    allowed_roles = [ROLE_ADMIN]

    def post(self, request, pk):
        target_user = get_object_or_404(CustomUser, pk=pk)
        if target_user == request.user:
            # Prevent self-deactivation
            return redirect(reverse('user_details', kwargs={'pk': pk}))
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=['is_active'])
        return redirect(reverse('user_details', kwargs={'pk': pk}))
