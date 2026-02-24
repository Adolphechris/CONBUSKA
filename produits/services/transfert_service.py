from django.db import transaction
from django.db.models import Sum, Case, When, IntegerField, F
from django.core.exceptions import ValidationError
from produits.models import MouvementStock, Stock, ReservationTransfertLot
from produits.services import StockService


class TransfertService:

    @staticmethod
    def reserver_fifo(*, transfert, magasin, article, qte):
        lots = (
            MouvementStock.objects
            .filter(magasin=magasin, article=article)
            .values("date_peremption")
            .annotate(
                qte_disponible=Sum(
                    Case(
                        When(type=MouvementStock.IN, then=F("qte")),
                        When(type=MouvementStock.OUT, then=-F("qte")),
                        output_field=IntegerField()
                    )
                )
            )
            .filter(qte_disponible__gt=0)
            .order_by("date_peremption")
        )

        reste = qte
        reservations = []

        for lot in lots:
            if reste <= 0:
                break

            consomme = min(lot["qte_disponible"], reste)

            reservations.append(
                ReservationTransfertLot(
                    transfert=transfert,
                    article=article,
                    date_peremption=lot["date_peremption"],
                    qte=consomme,
                )
            )
            reste -= consomme

        if reste > 0:
            raise ValidationError("Stock insuffisant (estimation)")

        ReservationTransfertLot.objects.bulk_create(reservations)


    @staticmethod
    @transaction.atomic
    def valider_transfert(transfert):
        """
        Cette methode permet de sortir les lots réservés et de faire des entrées dans le magasin
        destination
        :param transfert:
        :return:
        """
        reservations = (
            ReservationTransfertLot.objects
            .select_related("article")
            .filter(transfert=transfert)
            .order_by("date_peremption")
        )

        for r in reservations:
            StockService.sortir_stock_lot(
                magasin=transfert.magasin_source,
                article=r.article,
                date_peremption=r.date_peremption,
                qte=r.qte,
                source=transfert,
            )

            StockService.entrer_stock(
                magasin=transfert.magasin_destination,
                article=r.article,
                qte=r.qte,
                date_peremption=r.date_peremption,
                source=transfert,
            )

        transfert.valide = True
        transfert.save()