from django.contrib import admin
from .models import TypeFrais

@admin.register(TypeFrais)
class TypeFraisAdmin(admin.ModelAdmin):
    model = TypeFrais
    list_display = (
        "id",
        "nom",
        "icon",
        "actif",
    )
