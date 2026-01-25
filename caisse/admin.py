from django.contrib import admin
from .models import RubriqueCaisse, Caisse, SousRubriqueCaisse

@admin.register(RubriqueCaisse)
class RubriqueCaisseAdmin(admin.ModelAdmin):
    model = RubriqueCaisse
    list_display = (
        "id",
        "nom",
        "description",
        "visible",
    )


@admin.register(SousRubriqueCaisse)
class SousRubriqueCaisseAdmin(admin.ModelAdmin):
    model = SousRubriqueCaisse
    list_display = (
        "id",
        "rubrique",
        "nom",
        "description",
    )


@admin.register(Caisse)
class CaisseAdmin(admin.ModelAdmin):
    model = Caisse
    list_display = (
        "id",
        "nom",
        "is_principal",
    )