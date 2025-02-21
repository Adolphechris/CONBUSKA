from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import TypeProfile

CustomUser = get_user_model()


# class CustomUserAdmin(UserAdmin):
class CustomUserAdmin(admin.ModelAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'email', 'photo', 'telephone']


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(TypeProfile)
