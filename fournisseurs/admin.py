from django.contrib import admin
from .models import Fournisseur

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    model = Fournisseur
    list_display = (
        "id",
        "photo",
        "code",
        "nom",
        "type_frais",
        "is_system",
        "actif",
    )
