from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from caisse.models import (
    Caisse,
    CaisseCourante,
    MouvementCaisse,
    MouvementCaisseChargesExploitation,
    RubriqueCaisse,
    SousRubriqueCaisse,
)
from patrimoine.models import SnapshotJournalier
from patrimoine.services.journal_transaction_service import (
    JournalTransactionService,
)
from patrimoine.services.fonds_roulement_service import FondsRoulementService
from patrimoine.services.snapshot_service import SnapshotService
from patrimoine.views import (
    CalendrierFinancierView,
    ResultatsView,
    SuiviCapitauxView,
)

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


class FondsRoulementSignedBalancesTestCase(TestCase):
    def test_compute_tvms_valorise_le_stock_au_prix_de_vente(self):
        stocks = [
            SimpleNamespace(
                article=SimpleNamespace(
                    prix_vente=Decimal("150.00"),
                    devise="FC",
                ),
                qte=2,
            ),
            SimpleNamespace(
                article=SimpleNamespace(
                    prix_vente=Decimal("10.00"),
                    devise="$",
                ),
                qte=3,
            ),
        ]

        stock_manager = Mock()
        stock_manager.select_related.return_value.filter.return_value = stocks

        with patch(
            "produits.models.Stock.objects",
            new=stock_manager,
        ), patch.object(
            FondsRoulementService,
            "_get_taux",
            return_value=Decimal("2800.00"),
        ):
            total = FondsRoulementService._compute_tvms()

        self.assertEqual(total[0], Decimal("84300.00"))

    def test_compute_tscl_conserve_les_soldes_clients_negatifs(self):
        clients = [
            SimpleNamespace(solde_fc=lambda: Decimal("100.00")),
            SimpleNamespace(solde_fc=lambda: Decimal("-40.00")),
            SimpleNamespace(solde_fc=lambda: Decimal("0.00")),
        ]

        with patch("clients.models.Client.objects.all", return_value=clients):
            total = FondsRoulementService._compute_tscl()

        self.assertEqual(total, Decimal("60.00"))

    def test_compute_tscf_conserve_les_soldes_fournisseurs_negatifs(self):
        fournisseurs = [
            SimpleNamespace(solde_fc=lambda: Decimal("200.00")),
            SimpleNamespace(solde_fc=lambda: Decimal("-70.00")),
            SimpleNamespace(solde_fc=lambda: None),
        ]

        with patch(
            "fournisseurs.models.Fournisseur.objects.all",
            return_value=fournisseurs,
        ):
            total = FondsRoulementService._compute_tscf()

        self.assertEqual(total, Decimal("130.00"))


class PatrimoineChargeClassificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="patrimoine_charge_test",
            password="testpass123",
            force_password_change=False,
        )
        self.caisse = Caisse.objects.create(
            nom="Caisse Charges",
            is_principal=True,
        )
        self.caisse_courante = CaisseCourante.objects.create(
            caisse=self.caisse,
            ouvert_par=self.user,
            solde_initial=Decimal("1000.00"),
            est_ouverte=True,
        )
        self.rubrique_charges = RubriqueCaisse.objects.create(
            nom="Charges exploitation",
            description="Rubrique parent",
            visible=True,
            classification_metier=(
                RubriqueCaisse.ClassificationMetier.CHARGE_EXPLOITATION
            ),
        )
        self.sous_rubrique = SousRubriqueCaisse.objects.create(
            rubrique=self.rubrique_charges,
            nom="Electricite",
            description="Sous-rubrique test",
        )
        self.rubrique_transport = RubriqueCaisse.objects.create(
            nom="Transport",
            description="Rubrique autonome",
            visible=True,
            classification_metier=(
                RubriqueCaisse.ClassificationMetier.CHARGE_EXPLOITATION
            ),
        )

    def test_get_charges_exploitation_inclut_les_rubriques_autonomes_sans_doublon(
        self,
    ):
        date_mouvement = timezone.now()
        mouvement_lie = MouvementCaisse.objects.create(
            caisse=self.caisse_courante,
            type_mouvement="SORTIE",
            rubrique=self.rubrique_charges,
            montant=Decimal("100.00"),
            motif="Charge liee",
            effectue_par=self.user,
            date_mouvement=date_mouvement,
        )
        MouvementCaisseChargesExploitation.objects.create(
            mouvement_caisse=mouvement_lie,
            sous_rubrique=self.sous_rubrique,
        )
        MouvementCaisse.objects.create(
            caisse=self.caisse_courante,
            type_mouvement="SORTIE",
            rubrique=self.rubrique_transport,
            montant=Decimal("50.00"),
            motif="Transport agent",
            effectue_par=self.user,
            date_mouvement=date_mouvement,
        )

        details = ResultatsView().get_charges_exploitation(
            date_mouvement.month,
            date_mouvement.year,
        )

        self.assertEqual(
            details,
            [
                {"sous_rubrique__nom": "Electricite", "total": Decimal("100.00")},
                {"sous_rubrique__nom": "Transport", "total": Decimal("50.00")},
            ],
        )

    def test_compute_sj_inclut_les_rubriques_classees_dans_le_fr(self):
        date_reference = timezone.now().date()
        rubrique_creanciers = RubriqueCaisse.objects.create(
            nom="Créanciers",
            description="Remboursement creanciers",
            visible=True,
        )
        MouvementCaisse.objects.create(
            caisse=self.caisse_courante,
            type_mouvement="SORTIE",
            rubrique=self.rubrique_transport,
            montant=Decimal("50.00"),
            motif="Transport agent",
            effectue_par=self.user,
        )
        MouvementCaisse.objects.create(
            caisse=self.caisse_courante,
            type_mouvement="SORTIE",
            rubrique=rubrique_creanciers,
            montant=Decimal("20.00"),
            motif="Remboursement creancier",
            effectue_par=self.user,
        )

        total = FondsRoulementService.compute_sj(date_reference)

        self.assertEqual(total, Decimal("70.00"))

    @patch.object(
        FondsRoulementService,
        "compute_contreverification",
        return_value=Decimal("1000.00"),
    )
    @patch.object(
        FondsRoulementService,
        "compute_ej",
        return_value=Decimal("0.00"),
    )
    def test_rebuild_persiste_un_sj_avec_rubrique_classee(
        self,
        mock_compute_ej,
        mock_compute_contreverification,
    ):
        date_reference = timezone.now().date()
        MouvementCaisse.objects.create(
            caisse=self.caisse_courante,
            type_mouvement="SORTIE",
            rubrique=self.rubrique_transport,
            montant=Decimal("50.00"),
            motif="Transport agent",
            effectue_par=self.user,
        )

        FondsRoulementService.rebuild(date_reference)

        from patrimoine.models import FondsRoulementSnapshot

        snapshot = FondsRoulementSnapshot.objects.get(date=date_reference)
        self.assertEqual(snapshot.sj, Decimal("50.00"))
        self.assertEqual(snapshot.fr_final, Decimal("950.00"))


class SuiviCapitauxSignedDisplayTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="patrimoine_display_test",
            password="testpass123",
            force_password_change=False,
        )

    def test_get_context_data_conserve_les_signes_debiteurs_et_creanciers(self):
        request = self.factory.get("/patrimoine/capitaux/")
        request.user = self.user

        view = SuiviCapitauxView()
        view.request = request

        historique_qs = Mock()
        historique_qs.filter.return_value.order_by.return_value = []
        dernier_global_qs = Mock()
        dernier_global_qs.order_by.return_value.first.return_value = SimpleNamespace(
            fr_final=Decimal("1000.00"),
            fr_contreverif=Decimal("950.00"),
            ecart=Decimal("50.00"),
        )

        with patch(
            "patrimoine.models.FondsRoulementSnapshot.objects",
            new=Mock(
                filter=historique_qs.filter,
                order_by=dernier_global_qs.order_by,
            ),
        ), patch(
            "patrimoine.services.fonds_roulement_service."
            "FondsRoulementService.compute_contreverification_detail",
            return_value={
                "tvms": Decimal("0"),
                "tsc": Decimal("0"),
                "tscl": Decimal("-25.00"),
                "tscf": Decimal("-40.00"),
                "total": Decimal("15.00"),
            },
        ), patch(
            "creanciers.models.Debiteur.objects.all",
            return_value=[SimpleNamespace(solde_fc=lambda: Decimal("-25.00"))],
        ), patch(
            "creanciers.models.Creancier.objects.all",
            return_value=[SimpleNamespace(solde_fc=lambda: Decimal("-40.00"))],
        ):
            context = view.get_context_data()

        self.assertEqual(context["total_debiteurs"], Decimal("-25.00"))
        self.assertEqual(context["total_creanciers"], Decimal("-40.00"))
        self.assertEqual(context["fonds_propre"], Decimal("1015.00"))


class CalendrierFinancierViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="patrimoine_calendar_test",
            password="testpass123",
            force_password_change=False,
        )

    def test_get_context_data_affiche_le_net_journalier(self):
        request = self.factory.get("/patrimoine/calendrier/?mois=3&annee=2026")
        request.user = self.user

        view = CalendrierFinancierView()
        view.request = request

        snapshot_rows = [
            {
                "date": timezone.datetime(2026, 3, 5).date(),
                "total_entrees": Decimal("100.00"),
                "total_sorties": Decimal("40.00"),
                "solde_fermeture": Decimal("1500.00"),
            }
        ]

        daily_agg_qs = Mock()
        daily_agg_qs.values.return_value.annotate.return_value = snapshot_rows

        ordered_snapshots = Mock()
        ordered_snapshots.order_by.return_value = ordered_snapshots
        ordered_snapshots.aggregate.return_value = {
            "total_entrees": Decimal("100.00"),
            "total_sorties": Decimal("40.00"),
        }
        ordered_snapshots.first.return_value = SimpleNamespace(
            solde_fermeture=Decimal("1500.00")
        )
        ordered_snapshots.last.return_value = SimpleNamespace(
            solde_fermeture=Decimal("1500.00")
        )

        with patch(
            "patrimoine.models.SnapshotJournalier.objects",
            new=Mock(
                filter=Mock(
                    side_effect=[
                        daily_agg_qs,
                        ordered_snapshots,
                    ]
                )
            ),
        ), patch(
            "patrimoine.services.snapshot_service.SnapshotService.get_appro_par_jour",
            return_value={timezone.datetime(2026, 3, 5).date(): Decimal("20.00")},
        ), patch(
            "patrimoine.views.SnapshotService.get_appro_par_jour",
            return_value={timezone.datetime(2026, 3, 5).date(): Decimal("20.00")},
        ), patch(
            "patrimoine.views.SnapshotService.get_appro_total",
            return_value=Decimal("20.00"),
        ):
            context = view.get_context_data()

        day_data = next(
            day
            for week in context["weeks"]
            for day in week
            if day and day["date"] == timezone.datetime(2026, 3, 5).date()
        )

        self.assertEqual(day_data["entrees"], Decimal("120.00"))
        self.assertEqual(day_data["sorties"], Decimal("40.00"))
        self.assertEqual(day_data["solde"], Decimal("80.00"))
        self.assertEqual(context["solde_mois"], Decimal("1500.00"))
