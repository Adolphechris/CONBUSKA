from django.contrib import admin
from parametres.models import Magasin

@admin.register(Magasin)
class MagasinAdmin(admin.ModelAdmin):
    model = Magasin
    list_display = (
        "id",
        "nom",
        "description",
        "is_principal",
        "localisation",
    )
