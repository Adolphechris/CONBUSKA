from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum, F, IntegerField, Case, When
from produits.models import Magasin, MouvementStock
from produits.services import StockService
from factures.models import Facture, DetailsFacture


class FactureService:
    """
    Gestion des factures avec approche delta et verrouillage optimiste.

    CYCLE DE VIE D'UNE FACTURE :
    ┌─────────────────────────────────────────────────────────────────┐
    │  DRAFT (facture.valide = False)                                 │
    │    → Modifications de DetailsFacture uniquement                 │
    │    → Zéro mouvement de stock                                    │
    │    → Zéro compensatoire                                         │
    ├─────────────────────────────────────────────────────────────────┤
    │  valider()  ←  transition DRAFT → CONFIRMED                     │
    │    → 1 OUT net par (article, lot) via FIFO                      │
    │    → select_for_update() : verrouillage optimiste               │
    │    → Caissier A gagne, caissier B reçoit ValidationError propre │
    ├─────────────────────────────────────────────────────────────────┤
    │  CONFIRMED (facture.valide = True)                              │
    │    → modifier_article_facture() : approche delta O(1)           │
    │      delta > 0 → 1 OUT supplémentaire                           │
    │      delta < 0 → 1 IN de restitution                            │
    │      delta = 0 → aucun mouvement                                │
    └─────────────────────────────────────────────────────────────────┘

    AVANTAGES vs annuler/rejouer :
      - Phase draft   : 0 mouvement au lieu de O(n²) sur les scans.
      - Post-validation : 1 mouvement net au lieu de N compensatoires.
      - Verrouillage optimiste : conflits détectés à la validation,
        pas de réservation à gérer ni de tâche de nettoyage.
    """

    # ------------------------------------------------------------------
    # Helpers internes
    # ------------------------------------------------------------------

    @staticmethod
    def _annuler_mouvements_facture(facture: Facture):
        """
        Annule tous les mouvements liés à cette facture (usage : suppression).
        Délègue à StockService.annuler_mouvement pour la cohérence ledger.
        """
        mvts = MouvementStock.objects.filter(
            source_type=facture.__class__.__name__,
            source_id=facture.pk,
        )
        for mvt in mvts:
            StockService.annuler_mouvement(mvt)

    @staticmethod
    def _get_qte_confirmee(facture: Facture, article) -> int:
        """
        Retourne la quantité nette actuellement engagée en stock pour
        cet article sur cette facture, calculée depuis le ledger.

        Utilisé en phase CONFIRMED pour calculer le delta avant modification.
        """
        result = (
            MouvementStock.objects
            .filter(
                source_type=facture.__class__.__name__,
                source_id=facture.pk,
                article=article,
            )
            .aggregate(
                qte_nette=Sum(
                    Case(
                        When(type=MouvementStock.OUT, then=F("qte")),
                        When(type=MouvementStock.IN,  then=-F("qte")),
                        output_field=IntegerField(),
                    )
                )
            )["qte_nette"]
        )
        return result or 0

    # ------------------------------------------------------------------
    # API publique — saisie DRAFT (zéro mouvement stock)
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def ajouter_article_facture(facture: Facture, article, qte: int) -> DetailsFacture:
        """
        Ajoute un article ou incrémente sa quantité en phase DRAFT.

        Phase DRAFT  → mise à jour DetailsFacture uniquement, aucun mouvement stock.
        Phase CONFIRMED → délègue à modifier_article_facture (delta).
        """
        if qte <= 0:
            raise ValidationError("La quantité doit être strictement positive.")

        detail, _ = DetailsFacture.objects.get_or_create(
            facture=facture,
            article=article,
            defaults={"qte": 0, "prix": article.prix_vente},
        )

        nouvelle_qte = detail.qte + qte

        return FactureService.modifier_article_facture(facture, article, nouvelle_qte)

    @staticmethod
    @transaction.atomic
    def modifier_article_facture(facture: Facture, article, qte_nouvelle: int) -> DetailsFacture:
        """
        Modifie la quantité d'un article à une valeur précise.

        Phase DRAFT :
          → Met à jour DetailsFacture uniquement. Aucun mouvement stock.
            Le stock sera consommé en une seule fois à la validation.

        Phase CONFIRMED (approche delta) :
          → Calcule delta = qte_nouvelle - qte_ancienne_en_stock.
          → delta > 0 : 1 seul OUT supplémentaire (FIFO).
          → delta < 0 : 1 seul IN de restitution.
          → delta = 0 : aucun mouvement, uniquement mise à jour du prix.
          → Complexité : O(1) par modification, indépendamment de l'historique.

        Feedback anticipé en DRAFT via _verifier_stock_disponible() :
          → Vérification non bloquante pour UX (alerte immédiate si stock
            manifestement insuffisant), sans poser de verrou.
          → Le vrai contrôle bloquant reste dans sortir_stock_fifo() à la validation.
        """
        if qte_nouvelle < 0:
            raise ValidationError("La quantité ne peut pas être négative.")

        magasin = Magasin.objects.get(is_principal=True)

        detail, _ = DetailsFacture.objects.get_or_create(
            facture=facture,
            article=article,
            defaults={"qte": 0, "prix": article.prix_vente},
        )
        # qte_ancienne = detail.qte

        if not facture.valide:
            # ── Phase DRAFT : aucun mouvement stock ──────────────────────
            # Vérification indicative pour retour UX anticipé (sans verrou).
            if qte_nouvelle > 0:
                StockService._verifier_stock_disponible(magasin, article, qte_nouvelle)

        else:
            # ── Phase CONFIRMED : approche delta ─────────────────────────
            # qte_ancienne_stock = quantité nette actuellement en stock
            # pour cette facture (peut différer de detail.qte si des
            # corrections manuelles ont eu lieu hors service).
            qte_ancienne_stock = FactureService._get_qte_confirmee(facture, article)
            delta = qte_nouvelle - qte_ancienne_stock

            if delta > 0:
                # Besoin de stock supplémentaire → 1 seul OUT delta
                # select_for_update() dans sortir_stock_fifo() garantit
                # qu'un concurrent ne peut pas consommer le même stock.
                StockService.sortir_stock_fifo(
                    magasin=magasin,
                    article=article,
                    qte=delta,
                    source=facture,
                )
            elif delta < 0:
                # Surplus → 1 seul IN de restitution
                StockService.entrer_stock_delta(
                    magasin=magasin,
                    article=article,
                    qte=abs(delta),
                    source=facture,
                )
            # delta == 0 → aucun mouvement stock (ex: seul le prix change)

        # Mise à jour de la ligne de détail (draft ou confirmed)
        detail.qte = qte_nouvelle
        detail.prix = article.prix_vente
        detail.save(update_fields=["qte", "prix"])

        return detail

    @staticmethod
    @transaction.atomic
    def supprimer_article_facture(facture: Facture, article):
        """
        Retire un article de la facture.

        Phase DRAFT     → suppression de DetailsFacture uniquement, aucun stock touché.
        Phase CONFIRMED → restitue la quantité nette engagée avant de supprimer la ligne.
        """
        if facture.valide:
            qte_engagee = FactureService._get_qte_confirmee(facture, article)
            if qte_engagee > 0:
                magasin = Magasin.objects.get(is_principal=True)
                StockService.entrer_stock_delta(
                    magasin=magasin,
                    article=article,
                    qte=qte_engagee,
                    source=facture,
                )

        DetailsFacture.objects.filter(facture=facture, article=article).delete()

    # ------------------------------------------------------------------
    # API publique — transitions d'état
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def valider(*, facture: Facture, user):
        """
        Transition DRAFT → CONFIRMED.

        Génère exactement 1 mouvement OUT net par (article, lot) en FIFO,
        pour toutes les lignes de la facture.

        VERROUILLAGE OPTIMISTE :
          - select_for_update() dans sortir_stock_fifo() verrouille les lots
            consommés pour toute la durée de la transaction.
          - Si deux caissiers valident simultanément pour le même article :
              Caissier A → verrou posé → débite → COMMIT → verrou libéré.
              Caissier B → attend → lit le stock résiduel → ValidationError
                           si insuffisant → rollback propre → message clair.
          - Aucun risque de double consommation silencieuse.
          - Aucune réservation à gérer, aucune tâche de nettoyage.

        Idempotence : garde sur facture.valide empêche une double validation.
        """
        if facture.valide:
            raise ValidationError(
                "Cette facture est déjà validée. "
                "Utilisez modifier_article_facture() pour la modifier."
            )

        if not facture.facture_details.exists():
            raise ValidationError("Une facture sans articles ne peut pas être validée.")

        magasin = Magasin.objects.get(is_principal=True)

        # 1 OUT net par article (FIFO) — verrou optimiste posé ici
        for detail in facture.facture_details.select_related("article").all():
            if detail.qte <= 0:
                continue
            StockService.sortir_stock_fifo(
                magasin=magasin,
                article=detail.article,
                qte=detail.qte,
                source=facture,
            )

        facture.valide = True
        facture.actif = False
        facture.modifie_par = user
        facture.save(update_fields=["valide", "actif", "modifie_par"])

    @staticmethod
    @transaction.atomic
    def supprimer(*, facture: Facture):
        """
        Supprime la facture.

        Phase DRAFT     → aucun mouvement à annuler, suppression directe.
        Phase CONFIRMED → annule tous les mouvements via le ledger avant suppression.
        """
        if facture.valide:
            FactureService._annuler_mouvements_facture(facture)

        DetailsFacture.objects.filter(facture=facture).delete()
        facture.delete()