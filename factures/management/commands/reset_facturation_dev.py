from django.core.management.base import BaseCommand
from django.db import transaction
from esm import settings
from factures.models import Facture, DetailsFacture, FactureClient
from produits.models import MouvementStock
from produits.services import StockService


class Command(BaseCommand):
    help = "Reset complet de la facturation (DEV ONLY)"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Suppression des factures...")

        if not settings.DEBUG:
            raise Exception("Commande interdite en production.")

        self.stdout.write("Suppression DetailsFacture...")
        DetailsFacture.objects.all().delete()

        self.stdout.write("Suppression FactureClient...")
        FactureClient.objects.all().delete()

        self.stdout.write("Suppression Factures...")
        Facture.objects.all().delete()

        # 2️⃣ Supprimer tous les mouvements liés aux factures
        MouvementStock.objects.filter(
            source_type="Facture"
        ).delete()

        # 3️⃣ Rebuild snapshot depuis ledger restant
        StockService.rebuild_stock_snapshot()

        self.stdout.write(self.style.SUCCESS("Reset terminé."))