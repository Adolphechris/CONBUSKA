from datetime import date

from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from caisse.models import MouvementCaisse
from patrimoine.services import SnapshotService


class Command(BaseCommand):
    help = "Regenerer les snapshots journaliers des mouvements antérieurs"

    def handle(self, *args, **options):
        start_date = date(2025, 1, 1)
        mouvements = (
            MouvementCaisse.objects
            .filter(date_mouvement__date__gte=start_date)
            .select_related("caisse")
            .order_by("date_mouvement")
        )

        processed = set()
        success_count = 0
        skipped_count = 0
        error_count = 0

        for mvt in mouvements:
            key = (mvt.caisse_id, mvt.date_mouvement.date())
            if key in processed:
                skipped_count += 1
                continue

            try:
                SnapshotService.rebuild_day(
                    caisse_courante=mvt.caisse,
                    date=mvt.date_mouvement.date(),
                )
                processed.add(key)
                success_count += 1
            except ValidationError as exc:
                error_count += 1
                self.stderr.write(
                    f"[ERREUR] CaisseCourante={mvt.caisse_id} date={mvt.date_mouvement.date()} : {exc}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé : {success_count} snapshot(s) journalier(s) recalculé(s), "
                f"{skipped_count} mouvement(s) ignoré(s) car déjà couverts, "
                f"{error_count} erreur(s)."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Pensez à lancer ensuite : python manage.py rebuild_fonds_roulement"
            )
        )