from django.core.management.base import BaseCommand
from approvisionnements.models import Approvisionnement
from patrimoine.services import SnapshotService
from django.core.exceptions import ValidationError
from datetime import date
from django.db import transaction


class Command(BaseCommand):
    help = "Regenerer les snapshots des approvisionnements antérieurs"

    @transaction.atomic
    def handle(self, *args, **options):
        start_date = date(2025, 1, 1)
        approvisionnements = Approvisionnement.objects.filter(date_creation__date__gte=start_date)

        for appro in approvisionnements:
            try:
                SnapshotService.resultat_approvisionnement(
                    approvisionnement=appro,
                    date=appro.date_creation.date()
                )
            except ValidationError as e:
                self.stderr.write(
                    f"[ERREUR] Approvisionnement {appro.id} : {e}"
                )
