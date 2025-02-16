from django.urls import path
from .views import UserProfileView, UserProfileEditView, UserPasswordChangeView

urlpatterns = [
    path('user', UserProfileView.as_view(), name='user_profile'),
    path('user/edit', UserProfileEditView.as_view(), name='user_profile_update'),
    path('user/password/change', UserPasswordChangeView.as_view(), name='user_password_change'),
]