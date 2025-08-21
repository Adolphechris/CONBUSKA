from django.contrib import admin
from .models import Livreur


@admin.register(Livreur)
class LivreurAdmin(admin.ModelAdmin):
    model = Livreur
    list_display = (
        "id",
        "nom",
    )
