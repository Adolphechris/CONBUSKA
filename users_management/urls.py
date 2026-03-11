from django.urls import path
from .views import (
    UsersView, UserDetailsView, UserCreateView,
    UserEditView, UserSetPasswordView, UserToggleActiveView,
)

urlpatterns = [
    path('', UsersView.as_view(), name='users'),
    path('<int:pk>', UserDetailsView.as_view(), name='user_details'),
    path('create', UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/edit', UserEditView.as_view(), name='user_update'),
    path('<int:pk>/set_password', UserSetPasswordView.as_view(), name='user_set_password'),
    path('<int:pk>/toggle_active', UserToggleActiveView.as_view(), name='user_toggle_active'),
]
