from django.db import transaction
from django.core.exceptions import ValidationError
from produits.models import MouvementStock, Stock, ReservationTransfertLot
from produits.services import StockService


class TransfertService:
    """
    Règles d'architecture :
    - reserver_fifo() lit depuis le snapshot Stock (source de vérité unique,
      cohérente avec StockService) et pose des verrous select_for_update().
    - valider_transfert() est idempotent via une garde sur transfert.valide
      combinée à un select_for_update() sur le Transfert.
    - Chaque sortie/entrée conserve la date_peremption du lot réservé
      (traçabilité lot bout en bout).
    """

    @staticmethod
    @transaction.atomic
    def reserver_fifo(*, transfert, magasin, article, qte: int):
        """
        Réserve le stock nécessaire lot par lot (FIFO) pour un transfert.

        Corrections apportées :
        - Lecture depuis Stock (snapshot) et non MouvementStock (ledger brut),
          pour rester cohérent avec la source de vérité utilisée par StockService.
        - select_for_update() sur les lots pour bloquer les réservations concurrentes.
        - Méthode entourée de @transaction.atomic pour que les ReservationTransfertLot
          ne soient jamais persistés si la validation de stock échoue.
        """
        if qte <= 0:
            raise ValidationError("La quantité à réserver doit être strictement positive.")

        # Lecture + verrou depuis le snapshot (cohérent avec sortir_stock_fifo)
        lots = (
            Stock.objects
            .select_for_update()
            .filter(magasin=magasin, article=article, qte__gt=0)
            .order_by("date_peremption")
        )

        reste = qte
        reservations = []

        for lot in lots:
            if reste <= 0:
                break

            consomme = min(lot.qte, reste)

            reservations.append(
                ReservationTransfertLot(
                    transfert=transfert,
                    article=article,
                    date_peremption=lot.date_peremption,  # ← traçabilité lot
                    qte=consomme,
                )
            )

            reste -= consomme

        if reste > 0:
            raise ValidationError(
                f"Stock insuffisant pour '{article}' dans '{magasin}' "
                f"(manque {reste} unité(s))."
            )

        ReservationTransfertLot.objects.bulk_create(reservations)

    @staticmethod
    @transaction.atomic
    def annuler_reservations(transfert):
        """
        Supprime toutes les réservations d'un transfert non encore validé.
        Doit être appelé avant supprimer() ou en cas d'abandon.
        """
        ReservationTransfertLot.objects.filter(transfert=transfert).delete()

    @staticmethod
    @transaction.atomic
    def valider_transfert(transfert):
        """
        Exécute les mouvements de stock correspondant aux réservations :
          - Sortie dans le magasin source.
          - Entrée dans le magasin destination.

        Idempotence : un select_for_update() sur le Transfert combiné à une
        garde sur transfert.valide empêche tout double traitement (double-clic,
        retry réseau, tâche Celery rejouée).

        Traçabilité lot : la date_peremption de chaque réservation est transmise
        aux MouvementStock OUT et IN, garantissant la traçabilité bout en bout.
        """
        # Recharger avec verrou exclusif pour prévenir la double validation concurrente
        from produits.models import TransfertStock  # import local pour éviter la circularité
        transfert = TransfertStock.objects.select_for_update().get(pk=transfert.pk)

        if transfert.valide:
            # Idempotent : déjà validé, ne rien faire
            return

        reservations = (
            ReservationTransfertLot.objects
            .select_related("article")
            .filter(transfert=transfert)
            .order_by("date_peremption")
        )

        if not reservations.exists():
            raise ValidationError("Ce transfert ne contient aucune réservation.")

        for r in reservations:
            # Sortie depuis le magasin source (lot ciblé par date_peremption)
            StockService.sortir_stock_lot(
                magasin=transfert.magasin_source,
                article=r.article,
                date_peremption=r.date_peremption,      # ← traçabilité lot conservée
                qte=r.qte,
                source=transfert,
            )

            # Entrée dans le magasin destination (même lot, même date_peremption)
            StockService.entrer_stock(
                magasin=transfert.magasin_destination,
                article=r.article,
                qte=r.qte,
                date_peremption=r.date_peremption,      # ← traçabilité lot conservée
                source=transfert,
            )

        transfert.valide = True
        transfert.save(update_fields=["valide"])

    @staticmethod
    @transaction.atomic
    def annuler_transfert(transfert):
        """
        Annule un transfert déjà validé en inversant tous ses mouvements de stock.
        Idempotent via StockService.annuler_mouvement (héritage source_type/source_id).
        """
        from produits.models import TransfertStock  # import local pour éviter la circularité
        transfert = TransfertStock.objects.select_for_update().get(pk=transfert.pk)

        if not transfert.valide:
            raise ValidationError("Seul un transfert validé peut être annulé.")

        mvts = MouvementStock.objects.filter(
            source_type=transfert.__class__.__name__,
            source_id=transfert.pk,
        )
        for mvt in mvts:
            StockService.annuler_mouvement(mvt)

        transfert.valide = False
        transfert.save(update_fields=["valide"])