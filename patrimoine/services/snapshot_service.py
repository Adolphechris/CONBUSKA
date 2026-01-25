from caisse.models import MouvementCaisse, CaisseCourante
from approvisionnements.models import Approvisionnement
from patrimoine.models import SnapshotJournalier, ResultatApprovisionnementSnapshot, ResultatJournalier, ResultatMensuel
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum


class SnapshotService:

    EXCLUDED_RUBRIQUES = {"clients", "fournisseurs"}

    @staticmethod
    @transaction.atomic
    def rebuild_day(*, caisse_courante: CaisseCourante, date):
        caisse = caisse_courante.caisse

        if SnapshotJournalier.objects.filter(
            caisse=caisse, date=date, est_cloture=True
        ).exists():
            raise ValidationError("Journée déjà clôturée")

        mouvements = (
            MouvementCaisse.objects
            .select_related("rubrique")
            .filter(
                caisse=caisse_courante,
                date_mouvement__date=date,
            )
            .exclude(
                rubrique__nom__in=SnapshotService.EXCLUDED_RUBRIQUES
            )
        )

        total_entrees = (
                mouvements.filter(type_mouvement="ENTREE")
                .aggregate(total=Sum("montant"))["total"] or 0
        )

        total_sorties = (
                mouvements.filter(type_mouvement="SORTIE")
                .aggregate(total=Sum("montant"))["total"] or 0
        )

        previous = (
            SnapshotJournalier.objects
            .filter(caisse=caisse, date__lt=date)
            .order_by("-date")
            .first()
        )

        solde_ouverture = (
            previous.solde_fermeture
            if previous
            else caisse_courante.solde_initial
        )

        SnapshotJournalier.objects.update_or_create(
            caisse=caisse,
            date=date,
            defaults={
                "solde_ouverture": solde_ouverture,
                "total_entrees": total_entrees,
                "total_sorties": total_sorties,
                "solde_fermeture": solde_ouverture + total_entrees - total_sorties,
            }
        )

    @staticmethod
    def capture_approvisionnement(*, approvisionnement:Approvisionnement, date):
        """
        Cette method génère un snapshot de résultat/CA pour chaque appro, un snapshot journalier et mensuel des appros
        :param approvisionnement:
        :param date:
        :return:
        """
        ResultatApprovisionnementSnapshot.objects.update_or_create(
            approvisionnement=approvisionnement,
            date=date,
            defaults={
                "devise": approvisionnement.devise,
                "taux": approvisionnement.taux,
                "resultat_brut": approvisionnement.resultat_total,
                "cout_achat": approvisionnement.cout_achat,
                "frais_achat": approvisionnement.frais_achat_total,
                "chiffre_affaires": approvisionnement.chiffre_affaires,
            }
        )

    @staticmethod
    def rebuild_journalier(date):
        agg = ResultatApprovisionnementSnapshot.objects.filter(
            date=date
        ).aggregate(
            resultat_brut=Sum("resultat_brut"),
            chiffre_affaires=Sum("chiffre_affaires"),
        )

        ResultatJournalier.objects.update_or_create(
            date=date,
            defaults={
                "resultat_brut": agg["resultat_brut"] or 0,
                "chiffre_affaires": agg["chiffre_affaires"] or 0,
            }
        )

    @staticmethod
    def rebuild_mensuel(annee: int, mois: int):
        agg = ResultatApprovisionnementSnapshot.objects.filter(
            date__year=annee,
            date__month=mois,
        ).aggregate(
            resultat_brut=Sum("resultat_brut"),
            chiffre_affaires=Sum("chiffre_affaires"),
        )

        ResultatMensuel.objects.update_or_create(
            annee=annee,
            mois=mois,
            defaults={
                "resultat_brut": agg["resultat_brut"] or 0,
                "chiffre_affaires": agg["chiffre_affaires"] or 0,
            }
        )

    @staticmethod
    def on_approvisionnement_validated(approvisionnement: Approvisionnement):
        snapshot_date = approvisionnement.date_creation.date()

        SnapshotService.capture_approvisionnement(
            approvisionnement=approvisionnement,
            date=snapshot_date
        )

        SnapshotService.rebuild_journalier(snapshot_date)
        SnapshotService.rebuild_mensuel(
            snapshot_date.year,
            snapshot_date.month
        )

    @staticmethod
    def on_approvisionnement_rollback(approvisionnement: Approvisionnement):
        snapshot_date = approvisionnement.date_creation.date()

        ResultatApprovisionnementSnapshot.objects.filter(
            approvisionnement=approvisionnement
        ).delete()

        SnapshotService.rebuild_journalier(snapshot_date)
        SnapshotService.rebuild_mensuel(
            snapshot_date.year,
            snapshot_date.month
        )