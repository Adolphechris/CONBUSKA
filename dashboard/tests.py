from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from caisse.models import Caisse, CaisseCourante, MouvementCaisse, RubriqueCaisse
from dashboard.views import DashboardAdminView
from factures.tests.factories import (
    ClientFactory,
    DetailsFactureFactory,
    FactureClientFactory,
    FactureFactory,
)

User = get_user_model()


class DashboardSoldeCaissesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dashboard_test",
            password="testpass123",
            force_password_change=False,
        )
        self.rubrique = RubriqueCaisse.objects.create(
            nom="Divers",
            description="Rubrique de test",
            visible=True,
        )

    def _create_caisse_courante(self, *, nom: str, is_principal: bool):
        caisse = Caisse.objects.create(nom=nom, is_principal=is_principal)
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse,
            ouvert_par=self.user,
            solde_initial=Decimal("1000.00"),
            est_ouverte=True,
        )
        CaisseCourante.objects.filter(pk=caisse_courante.pk).update(
            date_ouverture=timezone.now()
        )
        caisse_courante.refresh_from_db()
        return caisse_courante

    def test_get_solde_caisses_inclut_ventes_comptoir_caisse_principale(self):
        caisse_courante = self._create_caisse_courante(
            nom="Caisse Principale",
            is_principal=True,
        )
        date_vente = caisse_courante.date_ouverture.date()

        MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="ENTREE",
            rubrique=self.rubrique,
            montant=Decimal("50.00"),
            motif="Entree diverse",
            effectue_par=self.user,
        )
        MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="SORTIE",
            rubrique=self.rubrique,
            montant=Decimal("20.00"),
            motif="Sortie diverse",
            effectue_par=self.user,
        )

        facture_comptoir = FactureFactory(
            cree_par=self.user,
            date_facture=date_vente,
            client_comptoir="Client comptoir",
            valide=True,
        )
        DetailsFactureFactory(
            facture=facture_comptoir,
            qte=2,
            prix=Decimal("100.00"),
        )

        facture_client = FactureFactory(
            cree_par=self.user,
            date_facture=date_vente,
            valide=True,
        )
        DetailsFactureFactory(
            facture=facture_client,
            qte=3,
            prix=Decimal("100.00"),
        )
        FactureClientFactory(
            facture=facture_client,
            client=ClientFactory(),
        )

        total, detail = DashboardAdminView.get_solde_caisses()

        self.assertEqual(total, Decimal("1230.00"))
        self.assertEqual(len(detail), 1)
        self.assertEqual(detail[0]["ventes"], Decimal("200.00"))
        self.assertEqual(detail[0]["solde"], Decimal("1230.00"))

    def test_get_solde_caisses_n_ajoute_pas_de_ventes_sur_caisse_secondaire(self):
        caisse_courante = self._create_caisse_courante(
            nom="Caisse Secondaire",
            is_principal=False,
        )

        facture = FactureFactory(
            cree_par=self.user,
            date_facture=caisse_courante.date_ouverture.date(),
            client_comptoir="Client comptoir",
            valide=True,
        )
        DetailsFactureFactory(
            facture=facture,
            qte=2,
            prix=Decimal("100.00"),
        )

        total, detail = DashboardAdminView.get_solde_caisses()

        self.assertEqual(total, Decimal("1000.00"))
        self.assertEqual(detail[0]["ventes"], Decimal("0"))
