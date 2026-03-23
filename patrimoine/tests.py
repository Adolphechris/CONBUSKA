from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from caisse.models import Caisse, CaisseCourante, MouvementCaisse, RubriqueCaisse
from patrimoine.models import SnapshotJournalier
from patrimoine.services.journal_transaction_service import (
    JournalTransactionService,
)
from patrimoine.services.snapshot_service import SnapshotService

User = get_user_model()


class PatrimoineTransfertExclusionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="patrimoine_test",
            password="testpass123",
            force_password_change=False,
        )
        self.caisse_source = Caisse.objects.create(
            nom="Caisse source",
            is_principal=True,
        )
        self.caisse_destination = Caisse.objects.create(
            nom="Caisse destination",
            is_principal=False,
        )
        self.caisse_courante_source = CaisseCourante.objects.create(
            caisse=self.caisse_source,
            ouvert_par=self.user,
            solde_initial=Decimal("1000.00"),
            est_ouverte=True,
        )
        self.caisse_courante_destination = CaisseCourante.objects.create(
            caisse=self.caisse_destination,
            ouvert_par=self.user,
            solde_initial=Decimal("500.00"),
            est_ouverte=True,
        )
        self.rubrique_transfert = RubriqueCaisse.objects.create(
            nom="Transfert caisse",
            description="Transfert inter-caisses",
            visible=True,
        )
        self.rubrique_divers = RubriqueCaisse.objects.create(
            nom="Divers",
            description="Rubrique diverse",
            visible=True,
        )

    def test_journal_transactions_exclut_les_transferts(self):
        date_mouvement = timezone.now()

        MouvementCaisse.objects.create(
            caisse=self.caisse_courante_source,
            type_mouvement="SORTIE",
            rubrique=self.rubrique_transfert,
            montant=Decimal("100.00"),
            motif="Transfert sortant",
            effectue_par=self.user,
            date_mouvement=date_mouvement,
        )
        MouvementCaisse.objects.create(
            caisse=self.caisse_courante_destination,
            type_mouvement="ENTREE",
            rubrique=self.rubrique_transfert,
            montant=Decimal("100.00"),
            motif="Transfert entrant",
            effectue_par=self.user,
            date_mouvement=date_mouvement,
        )
        mouvement_normal = MouvementCaisse.objects.create(
            caisse=self.caisse_courante_source,
            type_mouvement="ENTREE",
            rubrique=self.rubrique_divers,
            montant=Decimal("50.00"),
            motif="Versement divers",
            effectue_par=self.user,
            date_mouvement=date_mouvement,
        )

        lignes = JournalTransactionService.get_lines(
            date_mouvement.date(),
            date_mouvement.date(),
        )

        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0].motif, mouvement_normal.motif)
        self.assertEqual(lignes[0].rubrique_nom, "Divers")

    def test_snapshot_journalier_exclut_les_transferts(self):
        date_mouvement = timezone.now()

        MouvementCaisse.objects.create(
            caisse=self.caisse_courante_source,
            type_mouvement="ENTREE",
            rubrique=self.rubrique_transfert,
            montant=Decimal("200.00"),
            motif="Transfert entrant",
            effectue_par=self.user,
            date_mouvement=date_mouvement,
        )
        MouvementCaisse.objects.create(
            caisse=self.caisse_courante_source,
            type_mouvement="SORTIE",
            rubrique=self.rubrique_transfert,
            montant=Decimal("80.00"),
            motif="Transfert sortant",
            effectue_par=self.user,
            date_mouvement=date_mouvement,
        )
        MouvementCaisse.objects.create(
            caisse=self.caisse_courante_source,
            type_mouvement="ENTREE",
            rubrique=self.rubrique_divers,
            montant=Decimal("50.00"),
            motif="Entree normale",
            effectue_par=self.user,
            date_mouvement=date_mouvement,
        )
        MouvementCaisse.objects.create(
            caisse=self.caisse_courante_source,
            type_mouvement="SORTIE",
            rubrique=self.rubrique_divers,
            montant=Decimal("20.00"),
            motif="Sortie normale",
            effectue_par=self.user,
            date_mouvement=date_mouvement,
        )

        SnapshotService.rebuild_day(
            caisse_courante=self.caisse_courante_source,
            date=date_mouvement.date(),
        )

        snapshot = SnapshotJournalier.objects.get(
            caisse=self.caisse_source,
            date=date_mouvement.date(),
        )

        self.assertEqual(snapshot.total_entrees, Decimal("50.00"))
        self.assertEqual(snapshot.total_sorties, Decimal("20.00"))
        self.assertEqual(snapshot.solde_fermeture, Decimal("1030.00"))
