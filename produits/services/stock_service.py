from django.db import transaction
from django.db.models import Sum, Case, When, IntegerField, F
from django.core.exceptions import ValidationError
from produits.models import MouvementStock, Stock


class StockService:
    """
    Architecture ledger + snapshot avec verrouillage optimiste.

    PRINCIPES :
    ┌─────────────────────────────────────────────────────────────────┐
    │  MouvementStock  →  ledger immuable (append-only)               │
    │  Stock           →  snapshot temps réel (cache cohérent)        │
    └─────────────────────────────────────────────────────────────────┘

    VERROUILLAGE OPTIMISTE :
      - Aucune réservation en phase draft → zéro overhead en saisie.
      - À la validation, select_for_update() sur les lignes Stock garantit
        que le premier thread qui valide gagne ; le second reçoit une
        ValidationError propre si le stock a été consommé entre-temps.
      - Le conflit est détecté au plus tôt possible dans la transaction,
        avant toute écriture dans MouvementStock.

    APPROCHE DELTA (post-validation) :
      - entrer_stock_delta() et sortir_stock_fifo() écrivent exactement
        1 mouvement net par opération, quelle que soit l'historique.
      - Pas de compensatoire en cascade : O(1) par modification.

    RÈGLE LEDGER :
      - annuler_mouvement() fait hériter (source_type, source_id) au
        compensatoire → les filtres d'annulation futurs restent cohérents.
      - date_peremption conservée sur chaque mouvement → traçabilité lot.
    """

    # ------------------------------------------------------------------
    # Primitives internes
    # ------------------------------------------------------------------

    @staticmethod
    def _update_stock_snapshot(magasin, article, date_peremption, qte_delta: int):
        """
        Met à jour le snapshot Stock pour un lot donné.

        Séquence get_or_create → select_for_update().get() :
          1. get_or_create garantit que la ligne existe avant le verrou
             (un SELECT FOR UPDATE sur une ligne inexistante ne bloque rien).
          2. select_for_update() pose un verrou exclusif sur la ligne,
             bloquant toute autre transaction concurrente sur ce lot précis.

        Doit toujours être appelée à l'intérieur d'une transaction atomique
        parente (le verrou est libéré au COMMIT).
        """
        Stock.objects.get_or_create(
            magasin=magasin,
            article=article,
            date_peremption=date_peremption,
            defaults={"qte": 0},
        )

        stock_obj = Stock.objects.select_for_update().get(
            magasin=magasin,
            article=article,
            date_peremption=date_peremption,
        )

        stock_obj.qte += qte_delta

        if stock_obj.qte < 0:
            raise ValidationError(
                f"Stock insuffisant pour '{article}' "
                f"(lot {date_peremption}, magasin '{magasin}')."
            )
        elif stock_obj.qte == 0:
            stock_obj.delete()
        else:
            stock_obj.save(update_fields=["qte"])

    @staticmethod
    def _verifier_stock_disponible(magasin, article, qte_demandee: int):
        """
        Vérification rapide NON bloquante — usage : feedback anticipé en saisie.

        ⚠️  Indicatif uniquement : le stock peut changer entre cette lecture
        et la validation. Le vrai contrôle bloquant est dans sortir_stock_fifo()
        via select_for_update(). Ne jamais utiliser comme garde définitive.
        """
        total = (
            Stock.objects
            .filter(magasin=magasin, article=article, qte__gt=0)
            .aggregate(total=Sum("qte"))["total"] or 0
        )
        if total < qte_demandee:
            raise ValidationError(
                f"Stock insuffisant pour '{article}' dans '{magasin}' : "
                f"disponible {total}, demandé {qte_demandee}."
            )

    # ------------------------------------------------------------------
    # API publique — entrées / sorties
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def entrer_stock(*, magasin, article, qte: int, date_peremption, source) -> MouvementStock:
        """
        Entrée de stock (réception d'approvisionnement, restitution post-annulation).
        1 appel → 1 MouvementStock IN → snapshot mis à jour.
        """
        if qte <= 0:
            raise ValidationError("La quantité d'entrée doit être strictement positive.")

        mvt = MouvementStock.objects.create(
            magasin=magasin,
            article=article,
            type=MouvementStock.IN,
            qte=qte,
            date_peremption=date_peremption,
            source_type=source.__class__.__name__,
            source_id=source.pk,
        )

        StockService._update_stock_snapshot(magasin, article, date_peremption, +qte)

        return mvt

    @staticmethod
    @transaction.atomic
    def entrer_stock_delta(*, magasin, article, qte: int, source, date_peremption=None) -> MouvementStock:
        """
        Restitue une quantité au stock suite à une réduction post-validation
        (approche delta — O(1), pas de compensatoire en cascade).

        Utilisé par FactureService.modifier_article_facture() lorsque
        delta = qte_nouvelle - qte_ancienne < 0.

        Si date_peremption est None, restitution sur le lot le plus récent
        (LIFO sur les lots actifs) — convention standard pour les retours partiels.
        """
        if qte <= 0:
            raise ValidationError("La quantité de restitution doit être strictement positive.")

        if date_peremption is None:
            lot_cible = (
                Stock.objects
                .filter(magasin=magasin, article=article, qte__gt=0)
                .order_by("-date_peremption")
                .first()
            )
            if lot_cible is None:
                raise ValidationError(
                    f"Impossible de restituer : aucun lot actif pour '{article}' "
                    f"dans '{magasin}'. Précisez une date_peremption."
                )
            date_peremption = lot_cible.date_peremption

        mvt = MouvementStock.objects.create(
            magasin=magasin,
            article=article,
            type=MouvementStock.IN,
            qte=qte,
            date_peremption=date_peremption,
            source_type=source.__class__.__name__,
            source_id=source.pk,
        )

        StockService._update_stock_snapshot(magasin, article, date_peremption, +qte)

        return mvt

    @staticmethod
    @transaction.atomic
    def sortir_stock_fifo(*, magasin, article, qte: int, source) -> list[MouvementStock]:
        """
        Consomme le stock lot par lot (FIFO sur date_peremption).

        VERROUILLAGE OPTIMISTE :
          - select_for_update() pose un verrou exclusif sur chaque ligne Stock
            consommée dans l'ordre FIFO.
          - Caissier A valide → verrou posé → stock débité → COMMIT → verrou libéré.
          - Caissier B valide (concurrent) → attend le COMMIT de A → lit le stock
            résiduel réel → ValidationError si insuffisant → rollback propre.
          - Aucun risque de double consommation silencieuse.

        1 lot consommé → 1 MouvementStock OUT (traçabilité par lot).
        """
        if qte <= 0:
            raise ValidationError("La quantité de sortie doit être strictement positive.")

        lots = (
            Stock.objects
            .select_for_update()                         # ← verrou optimiste
            .filter(magasin=magasin, article=article, qte__gt=0)
            .order_by("date_peremption")                 # ← FIFO
        )

        reste = qte
        mouvements_crees: list[MouvementStock] = []

        for lot in lots:
            if reste <= 0:
                break

            consomme = min(lot.qte, reste)

            mvt = MouvementStock.objects.create(
                magasin=magasin,
                article=article,
                type=MouvementStock.OUT,
                qte=consomme,
                date_peremption=lot.date_peremption,     # ← traçabilité lot
                source_type=source.__class__.__name__,
                source_id=source.pk,
            )
            mouvements_crees.append(mvt)

            StockService._update_stock_snapshot(
                magasin, article, lot.date_peremption, -consomme
            )

            reste -= consomme

        if reste > 0:
            raise ValidationError(
                f"Stock insuffisant pour '{article}' dans '{magasin}' "
                f"(manque {reste} unité(s)). "
                f"Un autre caissier a peut-être validé une facture pour cet article."
            )

        return mouvements_crees

    @staticmethod
    @transaction.atomic
    def sortir_stock_lot(*, magasin, article, date_peremption, qte: int, source) -> MouvementStock:
        """
        Sortie ciblée sur un lot précis (transferts inter-magasins).
        Source de vérité : snapshot Stock.
        """
        if qte <= 0:
            raise ValidationError("La quantité de sortie doit être strictement positive.")

        try:
            stock_lot = Stock.objects.select_for_update().get(
                magasin=magasin,
                article=article,
                date_peremption=date_peremption,
            )
        except Stock.DoesNotExist:
            raise ValidationError(
                f"Lot introuvable pour '{article}' (péremption {date_peremption}) "
                f"dans '{magasin}'."
            )

        if stock_lot.qte < qte:
            raise ValidationError(
                f"Stock insuffisant pour '{article}' (lot {date_peremption}) : "
                f"disponible {stock_lot.qte}, demandé {qte}."
            )

        mvt = MouvementStock.objects.create(
            magasin=magasin,
            article=article,
            type=MouvementStock.OUT,
            qte=qte,
            date_peremption=date_peremption,             # ← traçabilité lot
            source_type=source.__class__.__name__,
            source_id=source.pk,
        )

        StockService._update_stock_snapshot(magasin, article, date_peremption, -qte)

        return mvt

    # ------------------------------------------------------------------
    # API publique — annulation ledger
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def annuler_mouvement(mouvement: MouvementStock) -> MouvementStock:
        """
        Crée un mouvement compensatoire symétrique.

        RÈGLE LEDGER : le compensatoire hérite de (source_type, source_id)
        du mouvement original → un filtre futur sur la source métier retrouve
        tous les mouvements (originaux + compensatoires) et peut les annuler
        à nouveau de façon idempotente.

        date_peremption conservée → le bon lot est ciblé dans le snapshot.
        """
        type_compensatoire = (
            MouvementStock.IN
            if mouvement.type == MouvementStock.OUT
            else MouvementStock.OUT
        )
        delta_snapshot = (
            +mouvement.qte
            if mouvement.type == MouvementStock.OUT
            else -mouvement.qte
        )

        compensatoire = MouvementStock.objects.create(
            magasin=mouvement.magasin,
            article=mouvement.article,
            type=type_compensatoire,
            qte=mouvement.qte,
            date_peremption=mouvement.date_peremption,   # ← lot d'origine
            source_type=mouvement.source_type,            # ← héritage source métier
            source_id=mouvement.source_id,
            annule_mouvement=mouvement,                   # ← lien d'audit
        )

        StockService._update_stock_snapshot(
            mouvement.magasin,
            mouvement.article,
            mouvement.date_peremption,
            delta_snapshot,
        )

        return compensatoire

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def rebuild_stock_snapshot():
        """
        Reconstruit le snapshot Stock depuis le ledger MouvementStock.
        Usage : maintenance, migration, audit de cohérence uniquement.
        En fonctionnement normal le snapshot est tenu à jour en temps réel.
        """
        Stock.objects.all().delete()

        qs = (
            MouvementStock.objects
            .values("magasin", "article", "date_peremption")
            .annotate(
                qte=Sum(
                    Case(
                        When(type=MouvementStock.IN,  then=F("qte")),
                        When(type=MouvementStock.OUT, then=-F("qte")),
                        output_field=IntegerField(),
                    )
                )
            )
        )

        Stock.objects.bulk_create([
            Stock(
                magasin_id=row["magasin"],
                article_id=row["article"],
                date_peremption=row["date_peremption"],
                qte=row["qte"],
            )
            for row in qs
            if row["qte"] and row["qte"] > 0
        ])