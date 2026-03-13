"""
Management command : reset_uat_data
====================================
Supprime toutes les données transactionnelles pour préparer un serveur de
test (UAT) à une nouvelle campagne de recette utilisateur.

CONSERVE  : articles, catégories, unités, magasins, clients, fournisseurs,
            agents, créanciers, débiteurs, utilisateurs, caisses (entités),
            rubriques/sous-rubriques caisse, types de frais, paramètres.

SUPPRIME  : factures, approvisionnements, mouvements caisse, sessions caisse
            (CaisseCourante), snapshots patrimoine et stock, ledger stock.

GARDE en place : les transferts de stock (ils ont leur propre cycle de vie
            et n'impactent pas les modules factures/appros/caisse).

Sécurité : bloqué si settings.DEBUG est False.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from approvisionnements.models import (
    FraisApprovisionnement,
    DetailsApprovisionnement,
    Approvisionnement,
)
from factures.models import DetailsFacture, FactureClient, Facture
from caisse.models import MouvementCaisse, CaisseCourante
from patrimoine.models import (
    ResultatApprovisionnementSnapshot,
    SnapshotJournalier,
    SnapshotMensuel,
    ResultatJournalier,
    ResultatMensuel,
    FondsRoulementSnapshot,
)
from produits.models import MouvementStock
from produits.services import StockService


class Command(BaseCommand):
    help = "Reset complet des données transactionnelles (UAT / DEV ONLY)"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            raise Exception(
                "Commande interdite en production (DEBUG=False)."
            )

        self.stdout.write(self.style.WARNING(
            "⚠  Reset UAT — suppression de toutes les données transactionnelles..."
        ))

        # ------------------------------------------------------------------
        # 1. Patrimoine : snapshots liés aux approvisionnements
        # ------------------------------------------------------------------
        self._delete(ResultatApprovisionnementSnapshot, "ResultatApprovisionnementSnapshot")

        # ------------------------------------------------------------------
        # 2. Approvisionnements
        # ------------------------------------------------------------------
        self._delete(FraisApprovisionnement, "FraisApprovisionnement")
        self._delete(DetailsApprovisionnement, "DetailsApprovisionnement")
        self._delete(Approvisionnement, "Approvisionnement")

        # ------------------------------------------------------------------
        # 3. Factures
        # ------------------------------------------------------------------
        self._delete(DetailsFacture, "DetailsFacture")
        self._delete(FactureClient, "FactureClient")
        self._delete(Facture, "Facture")

        # ------------------------------------------------------------------
        # 4. Caisse — les tables de liaison (MouvementCaisse*) sont en
        #    CASCADE sur MouvementCaisse, une seule suppression suffit.
        # ------------------------------------------------------------------
        self._delete(MouvementCaisse, "MouvementCaisse (+ liaisons tiers en cascade)")
        self._delete(CaisseCourante, "CaisseCourante (sessions)")

        # ------------------------------------------------------------------
        # 5. Patrimoine — tous les snapshots calculés
        # ------------------------------------------------------------------
        self._delete(SnapshotJournalier, "SnapshotJournalier")
        self._delete(SnapshotMensuel, "SnapshotMensuel")
        self._delete(ResultatJournalier, "ResultatJournalier")
        self._delete(ResultatMensuel, "ResultatMensuel")
        self._delete(FondsRoulementSnapshot, "FondsRoulementSnapshot")

        # ------------------------------------------------------------------
        # 6. Stock — ledger + rebuild snapshot à zéro
        # ------------------------------------------------------------------
        self._delete(MouvementStock, "MouvementStock (ledger)")
        self.stdout.write("Reconstruction du snapshot Stock (sera vide)...")
        StockService.rebuild_stock_snapshot()

        self.stdout.write(self.style.SUCCESS(
            "✓ Reset UAT terminé. Toutes les données transactionnelles ont été supprimées."
        ))

    def _delete(self, model, label):
        count, _ = model.objects.all().delete()
        self.stdout.write(f"  Suppression {label} : {count} ligne(s)")
