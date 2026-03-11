from datetime import date

from django.core.management.base import BaseCommand

from approvisionnements.models import Approvisionnement
from patrimoine.services import SnapshotService
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = "Regenerer les snapshots des approvisionnements antérieurs"

    def handle(self, *args, **options):
        start_date = date(2025, 1, 1)
        approvisionnements = (
            Approvisionnement.objects
            .filter(date_creation__date__gte=start_date, valide=True)
            .order_by("date_creation")
        )

        success_count = 0
        error_count = 0

        for appro in approvisionnements:
            try:
                SnapshotService.capture_approvisionnement(
                    approvisionnement=appro,
                    date=appro.date_creation.date()
                )
                SnapshotService.rebuild_journalier(appro.date_creation.date())
                SnapshotService.rebuild_mensuel(
                    appro.date_creation.year,
                    appro.date_creation.month,
                )
                success_count += 1
            except ValidationError as e:
                error_count += 1
                self.stderr.write(
                    f"[ERREUR] Approvisionnement {appro.id} : {e}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé : {success_count} approvisionnement(s) traité(s), {error_count} erreur(s)."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Pensez à lancer ensuite : python manage.py rebuild_fonds_roulement"
            )
        )
