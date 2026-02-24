from django.db import transaction
from django.core.exceptions import ValidationError
from produits.models import Magasin, MouvementStock
from produits.services import StockService
from factures.models import Facture, DetailsFacture


class FactureService:

    @staticmethod
    def annuler_mouvements_precedents(facture: Facture):
        """
        Identifie tous les mouvements OUT liés à cette facture et crée
        des mouvements IN compensatoires pour restaurer le stock.
        """
        anciens = MouvementStock.objects.filter(
            source_type="Facture",
            source_id=facture.pk,
            type=MouvementStock.OUT,
        )

        for mvt in anciens:
            # On utilise le StockService pour annuler proprement (création d'un IN)
            # sans supprimer l'enregistrement original pour l'audit.
            StockService.annuler_mouvement(mvt)

    @staticmethod
    def rejouer_etat_courant(facture: Facture):
        """
        Parcourt les lignes de la facture et effectue les sorties de stock
        en suivant la règle FIFO.
        """
        # Note : On récupère le magasin "Alimentation" comme dans l'ancienne logique.
        # Idéalement, le magasin devrait être un attribut de la Facture.
        magasin = Magasin.objects.get(is_principal=True)

        for detail in facture.facture_details.all():
            StockService.sortir_stock_fifo(
                magasin=magasin,
                article=detail.article,
                qte=detail.qte,
                source=facture,
            )

    @staticmethod
    @transaction.atomic
    def valider(*, facture: Facture, user):
        """
        Valide la facture, recalcule le stock et fige l'état.
        """
        if not facture.facture_details.exists():
            raise ValidationError("Une facture sans articles ne peut pas être validée.")

        # Si la facture était déjà validée, on annule tout avant de rejouer
        # (Idempotence pour les modifications post-validation).
        if facture.valide:
            FactureService.annuler_mouvements_precedents(facture)

        # On re-applique les sorties de stock basées sur les quantités actuelles.
        FactureService.rejouer_etat_courant(facture)

        facture.valide = True
        facture.actif = False  # Une facture validée n'est plus "en cours".
        facture.modifie_par = user
        facture.save(update_fields=["valide", "actif", "modifie_par"])

        # Optionnel : SnapshotService.on_facture_validated(facture)

    @staticmethod
    @transaction.atomic
    def supprimer(*, facture: Facture):
        """
        Annule les impacts sur le stock avant de supprimer la facture.
        """
        FactureService.annuler_mouvements_precedents(facture)
        facture.delete()

    @staticmethod
    @transaction.atomic
    def ajouter_article_facture(facture, article, qte):
        """
        Ajoute un article à la facture.
        Si l'article existe déjà, on additionne la quantité.
        """
        # 1. Récupérer ou créer la ligne de détail
        detail, created = DetailsFacture.objects.get_or_create(
            facture=facture,
            article=article,
            defaults={'qte': 0, 'prix': article.prix_vente}
        )

        # 2. On calcule la nouvelle quantité totale pour cette ligne
        nouvelle_qte_totale = detail.qte + qte

        # 3. On utilise la logique de modification pour gérer le stock proprement
        # (Annuler l'ancien état et rejouer le nouveau)
        return FactureService.modifier_article_facture(facture, article, nouvelle_qte_totale)

    @staticmethod
    @transaction.atomic
    def modifier_article_facture(facture, article, qte):
        """
        Modifie la quantité d'un article par une nouvelle valeur précise.
        """
        magasin = Magasin.objects.get(is_principal=True)

        # 1. Annuler TOUS les mouvements OUT précédents de cet article pour cette facture
        mvts_existants = MouvementStock.objects.filter(
            source_type="Facture",
            source_id=facture.pk,
            article=article,
            type=MouvementStock.OUT
        )
        for mvt in mvts_existants:
            StockService.annuler_mouvement(mvt)

        # 2. Mise à jour de la ligne de détail (écrase la qte précédente)
        detail, _ = DetailsFacture.objects.update_or_create(
            facture=facture,
            article=article,
            defaults={'qte': qte, 'prix': article.prix_vente}
        )

        # 3. Sortie du stock (FIFO) pour la nouvelle quantité totale
        # Si le stock est insuffisant, l'exception ValidationError annulera la transaction.
        StockService.sortir_stock_fifo(
            magasin=magasin,
            article=article,
            qte=qte,
            source=facture
        )

        return detail

    @staticmethod
    @transaction.atomic
    def supprimer_article_facture(facture, article):
        """
        Supprime complètement un article de la facture et rend les produits au stock.
        """
        # 1. Annuler les mouvements de stock
        mvts_existants = MouvementStock.objects.filter(
            source_type="Facture",
            source_id=facture.pk,
            article=article,
            type=MouvementStock.OUT
        )
        for mvt in mvts_existants:
            StockService.annuler_mouvement(mvt)

        # 2. Supprimer la ligne de détail
        DetailsFacture.objects.filter(facture=facture, article=article).delete()
