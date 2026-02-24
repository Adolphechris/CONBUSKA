from django.db import transaction
from django.db.models import Sum, Case, When, IntegerField, F
from django.core.exceptions import ValidationError
from produits.models import MouvementStock, Stock


class StockService:

    @staticmethod
    def _update_stock_snapshot(magasin, article, date_peremption, qte_delta):
        """
        Met à jour la table Stock. Verrouille la ligne traitée pour éviter
        les conflits si deux utilisateurs modifient le même stock en même temps.
        """
        # On utilise select_for_update() pour bloquer les écritures concurrentes
        stock_obj, created = Stock.objects.select_for_update().get_or_create(
            magasin=magasin,
            article=article,
            date_peremption=date_peremption,
            defaults={'qte': 0}
        )

        stock_obj.qte += qte_delta

        if stock_obj.qte < 0:
            raise ValidationError(f"Stock insuffisant pour l'article {article.designation}")
        elif stock_obj.qte == 0:
            # On nettoie la base pour ne pas accumuler des lignes à stock 0
            stock_obj.delete()
        else:
            stock_obj.save()

    @staticmethod
    @transaction.atomic
    def entrer_stock(*, magasin, article, qte, date_peremption, source):
        mvt = MouvementStock.objects.create(
            magasin=magasin,
            article=article,
            type=MouvementStock.IN,
            qte=qte,
            date_peremption=date_peremption,
            source_type=source.__class__.__name__,
            source_id=source.id,
        )

        StockService._update_stock_snapshot(magasin, article, date_peremption, qte)

        return mvt

    @staticmethod
    @transaction.atomic
    def sortir_stock_fifo(*, magasin, article, qte, source):
        lots = (
            MouvementStock.objects
            .select_for_update()
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
        mouvements_crees = []

        for lot in lots:
            if reste <= 0:
                break

            consomme = min(lot["qte_disponible"], reste)

            mvt = MouvementStock.objects.create(
                magasin=magasin,
                article=article,
                type=MouvementStock.OUT,
                qte=consomme,
                date_peremption=lot["date_peremption"],
                source_type=source.__class__.__name__,
                source_id=source.id,
            )

            mouvements_crees.append(mvt)

            reste -= consomme

            StockService._update_stock_snapshot(
                magasin,
                article,
                lot["date_peremption"],
                -consomme
            )

        if reste > 0:
            raise ValidationError("Stock insuffisant")

        return mouvements_crees

    @staticmethod
    @transaction.atomic
    def sortir_stock_lot(*, magasin, article, date_peremption, qte, source):
        """
        Sort une quantité précise d'un lot donné (transfert)
        """
        disponible = (
            MouvementStock.objects
            .select_for_update()
            .filter(
                magasin=magasin,
                article=article,
                date_peremption=date_peremption
            )
            .aggregate(
                qte=Sum(
                    Case(
                        When(type=MouvementStock.IN, then=F("qte")),
                        When(type=MouvementStock.OUT, then=-F("qte")),
                        output_field=IntegerField()
                    )
                )
            )["qte"] or 0
        )

        if disponible < qte:
            raise ValidationError(
                f"Stock insuffisant pour {article} (lot {date_peremption})"
            )

        sortie = MouvementStock.objects.create(
            magasin=magasin,
            article=article,
            type=MouvementStock.OUT,
            qte=qte,
            date_peremption=date_peremption,
            source_type=source.__class__.__name__,
            source_id=source.id,
        )

        StockService._update_stock_snapshot(magasin, article, date_peremption, -qte)

        return sortie


    @staticmethod
    @transaction.atomic
    def annuler_mouvement(mouvement):
        MouvementStock.objects.create(
            magasin=mouvement.magasin,
            article=mouvement.article,
            type=MouvementStock.OUT if mouvement.type == MouvementStock.IN else MouvementStock.IN,
            qte=mouvement.qte,
            date_peremption=mouvement.date_peremption,
            source_type="ANNULATION",
            source_id=mouvement.id,
        )

        delta = mouvement.qte if mouvement.type == MouvementStock.OUT else -mouvement.qte

        StockService._update_stock_snapshot(
            mouvement.magasin,
            mouvement.article,
            mouvement.date_peremption,
            delta
        )

    @staticmethod
    @transaction.atomic
    def rebuild_stock_snapshot():
        Stock.objects.all().delete()

        qs = (
            MouvementStock.objects
            .values("magasin", "article", "date_peremption")
            .annotate(
                qte=Sum(
                    Case(
                        When(type=MouvementStock.IN, then=F("qte")),
                        When(type=MouvementStock.OUT, then=-F("qte")),
                        output_field=IntegerField()
                    )
                )
            )
        )

        Stock.objects.bulk_create([
            Stock(
                magasin_id=i["magasin"],
                article_id=i["article"],
                date_peremption=i["date_peremption"],
                qte=i["qte"],
            )
            for i in qs if i["qte"] > 0
        ])