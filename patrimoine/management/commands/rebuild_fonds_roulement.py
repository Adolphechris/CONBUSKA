import datetime
from django.core.management.base import BaseCommand
from django.db.models import Min, Max
from patrimoine.services.fonds_roulement_service import FondsRoulementService
from patrimoine.models import FondsRoulementSnapshot


class Command(BaseCommand):
    help = "Recalculer les snapshots du Fonds de Roulement sur une plage de dates"

    def add_arguments(self, parser):
        parser.add_argument(
            "--debut",
            type=lambda s: datetime.date.fromisoformat(s),
            help="Date de début (YYYY-MM-DD). Défaut : première date avec données.",
        )
        parser.add_argument(
            "--fin",
            type=lambda s: datetime.date.fromisoformat(s),
            help="Date de fin (YYYY-MM-DD). Défaut : aujourd'hui.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprimer les snapshots existants dans la plage avant de recalculer.",
        )

    def handle(self, *args, **options):
        from caisse.models import MouvementCaisse
        from patrimoine.models import ResultatJournalier

        # Déterminer la plage de dates
        date_debut = options.get("debut")
        date_fin = options.get("fin") or datetime.date.today()

        if date_debut is None:
            # Trouver la première date avec des données
            premiers = []
            mvt = MouvementCaisse.objects.aggregate(m=Min("date_mouvement__date"))["m"]
            if mvt:
                premiers.append(mvt)
            res = ResultatJournalier.objects.aggregate(m=Min("date"))["m"]
            if res:
                premiers.append(res)

            if not premiers:
                self.stderr.write("Aucune donnée trouvée. Spécifiez --debut.")
                return

            date_debut = min(premiers)

        if date_fin < date_debut:
            self.stderr.write("--fin doit être >= --debut.")
            return

        nb_jours = (date_fin - date_debut).days + 1
        self.stdout.write(
            f"Recalcul du FR du {date_debut} au {date_fin} ({nb_jours} jour(s))..."
        )

        if options.get("reset"):
            deleted, _ = FondsRoulementSnapshot.objects.filter(
                date__range=(date_debut, date_fin)
            ).delete()
            self.stdout.write(f"  {deleted} snapshot(s) supprimé(s).")

        # Traitement chronologique — indispensable car chaque jour dépend du précédent
        current = date_debut
        ok = 0
        errors = 0

        while current <= date_fin:
            try:
                FondsRoulementService.rebuild(current)
                ok += 1
            except Exception as e:
                self.stderr.write(f"  [ERREUR] {current} : {e}")
                errors += 1
            current += datetime.timedelta(days=1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé : {ok} snapshot(s) créé(s)/mis à jour, {errors} erreur(s)."
            )
        )
