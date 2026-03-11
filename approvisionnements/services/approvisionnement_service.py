from django.db import transaction
from django.core.exceptions import ValidationError
from approvisionnements.models import Approvisionnement, DetailsApprovisionnement
from patrimoine.services import SnapshotService
from produits.services import StockService
from produits.models import MouvementStock


class ApprovisionnementService:
    """
    Règles d'architecture :
    - Toute annulation de mouvement passe par StockService.annuler_mouvement,
      qui garantit la mise à jour du snapshot et l'héritage de la source métier.
    - valider() est idempotent : annule inconditionnellement avant de rejouer.
    - SnapshotService (patrimoine) est appelé après que le stock est cohérent.
    """

    @staticmethod
    def annuler_mouvements_precedents(approvisionnement: Approvisionnement):
        """
        Annule tous les mouvements de stock liés à cet approvisionnement.
        Délègue à StockService.annuler_mouvement pour :
          - Mettre à jour le snapshot Stock (bug corrigé : l'ancienne version
            créait les compensatoires manuellement sans toucher Stock).
          - Faire hériter (source_type, source_id) aux compensatoires, rendant
            les annulations successives idempotentes.
        """
        mvts = MouvementStock.objects.filter(
            source_type="Approvisionnement",
            source_id=approvisionnement.pk,
        )
        for mvt in mvts:
            StockService.annuler_mouvement(mvt)

    @staticmethod
    def rejouer_etat_courant(approvisionnement: Approvisionnement):
        """
        Crée les entrées de stock pour toutes les lignes de l'approvisionnement.
        La date_peremption de chaque détail est transmise et conservée sur le
        MouvementStock (traçabilité lot).
        """
        for detail in approvisionnement.detailsapprovisionnement_set.select_related("article").all():
            StockService.entrer_stock(
                magasin=approvisionnement.magasin,
                article=detail.article,
                qte=detail.qte,
                date_peremption=detail.date_peremption,  # ← traçabilité lot
                source=approvisionnement,
            )

    @staticmethod
    @transaction.atomic
    def valider(*, approvisionnement: Approvisionnement, user):
        """
        Valide l'approvisionnement et applique les entrées de stock.

        Idempotence : annule inconditionnellement tous les mouvements précédents
        avant de rejouer. Appelable N fois avec le même état final en base.

        SnapshotService est appelé après validation du stock pour garantir
        qu'il opère sur un snapshot cohérent.
        """
        if not approvisionnement.detailsapprovisionnement_set.exists():
            raise ValidationError(
                "Un approvisionnement sans articles ne peut pas être validé."
            )

        # Annulation inconditionnelle (idempotence)
        ApprovisionnementService.annuler_mouvements_precedents(approvisionnement)

        # Rejouer les entrées de stock
        ApprovisionnementService.rejouer_etat_courant(approvisionnement)

        approvisionnement.actif = False
        approvisionnement.valide = True
        approvisionnement.modifie_par = user
        approvisionnement.save(update_fields=["actif", "valide", "modifie_par"])

        # Mise à jour du prix d'achat (dernier coût réel enregistré)
        for detail in approvisionnement.detailsapprovisionnement_set.select_related("article").all():
            if detail.prix:
                detail.article.prix_achat = detail.prix
                detail.article.save(update_fields=["prix_achat"])

        # Appelé en dernier : le snapshot patrimoine lit un stock cohérent
        SnapshotService.on_approvisionnement_validated(approvisionnement)

    @staticmethod
    @transaction.atomic
    def supprimer(*, approvisionnement: Approvisionnement):
        """
        Annule les impacts stock puis supprime l'approvisionnement.
        SnapshotService est appelé avant delete() pour avoir accès aux données
        de l'approvisionnement (magasin, articles) encore en base.
        """
        ApprovisionnementService.annuler_mouvements_precedents(approvisionnement)

        # SnapshotService opère sur un stock déjà annulé et cohérent
        SnapshotService.on_approvisionnement_rollback(approvisionnement)

        DetailsApprovisionnement.objects.filter(approvisionnement=approvisionnement).delete()
        approvisionnement.delete()