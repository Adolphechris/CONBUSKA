from django.core.management.base import BaseCommand
from caisse.models import MouvementCaisse, Caisse, CaisseCourante
from patrimoine.services import enregistrer_mouvement
from django.core.exceptions import ValidationError
from datetime import date


class Command(BaseCommand):
    help = "Regenerer les snapshots journaliers des mouvements antérieurs"

    def handle(self, *args, **options):
        start_date = date(2025, 1, 1)
        mouvements = (
            MouvementCaisse.objects
            .filter(date_mouvement__date__gte=start_date)
            .order_by("date_mouvement")
        )

        for mvt in mouvements:
            try:
                enregistrer_mouvement(mvt)
            except ValidationError:
                continue