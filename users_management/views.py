from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from users.models import CustomUser
from .forms import UserCreateForm, UserEditForm, UserPasswordForm
from django.urls import reverse


class UsersView(LoginRequiredMixin, ListView):
    model = CustomUser
    context_object_name = 'users'
    template_name = 'users/users.html'


class UserDetailsView(LoginRequiredMixin, DetailView):
    model = CustomUser
    context_object_name = 'user_details'
    template_name = 'users/user_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class UserCreateView(LoginRequiredMixin, CreateView):
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


class UserEditView(LoginRequiredMixin, UpdateView):
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


class UserSetPasswordView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'users/user_set_password_form.html'
    context_object_name = 'user_password'
    form_class = UserPasswordForm
    success_url = reverse_lazy('users')

    def get_form_kwargs(self):
        kwargs = super(UserSetPasswordView, self).get_form_kwargs()
        kwargs['user'] = self.object
        print(kwargs)
        return kwargs
