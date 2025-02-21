"""
URL configuration for esm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog
from django.contrib.auth import views as auth_views
from users.forms import CustomAuthForm

urlpatterns = [
    path('admin/', admin.site.urls),
    # User management
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', auth_views.LoginView.as_view(authentication_form=CustomAuthForm)),
    path('', include('users.urls')),
    path('index/', include('dashboard.urls')),
    path('', include('dashboard.urls')),
    path('fournisseurs/', include('fournisseurs.urls')),
    path('users/', include('users_management.urls')),
    path('parametres/', include('parametres.urls')),
    path("select2/", include("django_select2.urls")),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='jsi18n'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
