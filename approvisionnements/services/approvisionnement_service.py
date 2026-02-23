from django.db import transaction
from approvisionnements.models import Approvisionnement
from patrimoine.services import SnapshotService
from produits.services import StockService
from produits.models import MouvementStock


class ApprovisionnementService:

    @staticmethod
    def annuler_mouvements_precedents(approvisionnement: Approvisionnement):
        anciens_mouvements = MouvementStock.objects.filter(
            source_type="Approvisionnement",
            source_id=approvisionnement.pk,
            type=MouvementStock.IN,
        )

        # MOUVEMENTS D'ANNULATION
        for mvt in anciens_mouvements:
            MouvementStock.objects.create(
                magasin=mvt.magasin,
                article=mvt.article,
                type=MouvementStock.OUT,
                qte=mvt.qte,
                date_peremption=mvt.date_peremption,
                source_type="ANNULATION_APPRO",
                source_id=approvisionnement.pk,
            )

    @staticmethod
    def rejouer_etat_courant(approvisionnement: Approvisionnement):
        for detail in approvisionnement.detailsapprovisionnement_set.all():
            StockService.entrer_stock(
                magasin=approvisionnement.magasin,
                article=detail.article,
                qte=detail.qte,
                date_peremption=detail.date_peremption,
                source=approvisionnement,
            )

    @staticmethod
    @transaction.atomic
    def valider(*, approvisionnement: Approvisionnement, user):
        if approvisionnement.valide:
            ApprovisionnementService.annuler_mouvements_precedents(approvisionnement)

        ApprovisionnementService.rejouer_etat_courant(approvisionnement)

        approvisionnement.actif = False
        approvisionnement.valide = True
        approvisionnement.modifie_par = user
        approvisionnement.save(update_fields=["actif", "valide", "modifie_par"])

        SnapshotService.on_approvisionnement_validated(approvisionnement)

    @staticmethod
    @transaction.atomic
    def supprimer(*, approvisionnement: Approvisionnement):
        ApprovisionnementService.annuler_mouvements_precedents(approvisionnement)
        SnapshotService.on_approvisionnement_rollback(approvisionnement)
        approvisionnement.delete()