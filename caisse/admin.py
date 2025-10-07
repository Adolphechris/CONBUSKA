from django.contrib import admin
from .models import RubriqueCaisse, Caisse

@admin.register(RubriqueCaisse)
class RubriqueCaisseAdmin(admin.ModelAdmin):
    model = RubriqueCaisse
    list_display = (
        "id",
        "nom",
        "description",
        "visible",
    )


@admin.register(Caisse)
class CaisseAdmin(admin.ModelAdmin):
    model = Caisse
    list_display = (
        "id",
        "nom",
        "is_principal",
    )