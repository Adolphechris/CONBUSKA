from django.db import transaction
from approvisionnements.models import Approvisionnement
from patrimoine.services import SnapshotService


class ApprovisionnementService:

    @staticmethod
    @transaction.atomic
    def valider(*, approvisionnement: Approvisionnement, user):
        if not approvisionnement.actif:
            return

        approvisionnement.actif = False
        approvisionnement.modifie_par = user
        approvisionnement.save(update_fields=["actif", "modifie_par"])

        SnapshotService.on_approvisionnement_validated(approvisionnement)

    @staticmethod
    @transaction.atomic
    def supprimer(*, approvisionnement: Approvisionnement):
        SnapshotService.on_approvisionnement_rollback(approvisionnement)
        approvisionnement.delete()