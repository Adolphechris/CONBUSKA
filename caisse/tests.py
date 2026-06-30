import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from caisse.forms import CaisseForm
from caisse.models import (
    Caisse,
    CaisseCourante,
    MouvementCaisse,
    RubriqueCaisse,
)
from caisse.selectors import get_total_ventes_caisse
from caisse.services.mouvement_caisse import MouvementCaisseService
from caisse.views import OuvertureCaisseView, rubrique_champ_view
from factures.tests.factories import (
    ClientFactory,
    DetailsFactureFactory,
    FactureClientFactory,
    FactureFactory,
)

User = get_user_model()


@patch("caisse.services.mouvement_caisse.FondsRoulementService")
@patch("caisse.services.mouvement_caisse.SnapshotService")
class MouvementCaisseServiceTestCase(TestCase):
    """Tests unitaires pour MouvementCaisseService (Phase 4)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            force_password_change=False,
        )
        self.caisse = Caisse.objects.create(nom="Caisse Source", is_principal=True)
        self.caisse_destination = Caisse.objects.create(nom="Caisse Destination", is_principal=False)
        self.caisse_destination_bis = Caisse.objects.create(nom="Caisse Destination 2", is_principal=False)
        self.rubrique = RubriqueCaisse.objects.create(
            nom="Divers",
            description="Rubrique diverse pour tests",
            visible=True,
        )
        self.rubrique_transfert = RubriqueCaisse.objects.create(
            nom="Transfert caisse",
            description="Rubrique transfert pour tests",
            visible=True,
        )

    def _create_caisse_courante(self, est_ouverte=True):
        return CaisseCourante.objects.create(
            caisse=self.caisse,
            solde_initial=Decimal("1000.00"),
            est_ouverte=est_ouverte,
        )

    def _create_caisse_destination_courante(self, *, caisse=None, est_ouverte=True):
        return CaisseCourante.objects.create(
            caisse=caisse or self.caisse_destination,
            solde_initial=Decimal("500.00"),
            est_ouverte=est_ouverte,
        )

    def _valid_form_data(self, caisse_pk):
        return {
            "type_mouvement": "ENTREE",
            "rubrique": str(self.rubrique.pk),
            "montant": "50.00",
            "motif": "Test mouvement",
        }

    def _transfer_form_data(self, montant="75.00", motif="Transfert test"):
        return {
            "type_mouvement": "SORTIE",
            "rubrique": str(self.rubrique_transfert.pk),
            "montant": montant,
            "motif": motif,
        }

    def test_create_caisse_ouverte_succes(self, mock_snapshot, mock_fonds):
        """Caisse ouverte : create crée un mouvement."""
        caisse_courante = self._create_caisse_courante(est_ouverte=True)
        form = CaisseForm(
            self._valid_form_data(self.caisse.pk),
            caisse_pk=caisse_courante.pk,
        )
        mouvement = MouvementCaisseService.create(
            form=form,
            caisse_courante=caisse_courante,
            user=self.user,
            skip_rebuild=True,
        )
        self.assertIsNotNone(mouvement.pk)
        self.assertEqual(mouvement.caisse, caisse_courante)
        self.assertEqual(mouvement.type_mouvement, "ENTREE")
        self.assertEqual(mouvement.montant, Decimal("50.00"))
        self.assertEqual(mouvement.motif, "Test mouvement")
        mock_snapshot.rebuild_day.assert_not_called()
        mock_fonds.rebuild.assert_not_called()

    def test_create_caisse_fermee_raise_validation_error(self, mock_snapshot, mock_fonds):
        """Caisse fermée : create lève ValidationError."""
        caisse_courante = self._create_caisse_courante(est_ouverte=False)
        form = CaisseForm(
            self._valid_form_data(self.caisse.pk),
            caisse_pk=caisse_courante.pk,
        )
        with self.assertRaises(ValidationError) as ctx:
            MouvementCaisseService.create(
                form=form,
                caisse_courante=caisse_courante,
                user=self.user,
                skip_rebuild=True,
            )
        self.assertIn("clôturée", str(ctx.exception))
        mock_snapshot.rebuild_day.assert_not_called()
        self.assertEqual(MouvementCaisse.objects.count(), 0)

    def test_update_caisse_fermee_raise_validation_error(self, mock_snapshot, mock_fonds):
        """Caisse fermée : update lève ValidationError."""
        caisse_courante = self._create_caisse_courante(est_ouverte=True)
        mouvement = MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="ENTREE",
            rubrique=self.rubrique,
            montant=Decimal("100.00"),
            motif="Mouvement initial",
            effectue_par=self.user,
        )
        caisse_courante.est_ouverte = False
        caisse_courante.save()
        form = CaisseForm(
            {
                "type_mouvement": "ENTREE",
                "rubrique": str(self.rubrique.pk),
                "montant": "150.00",
                "motif": "Modifié",
            },
            instance=mouvement,
            caisse_pk=caisse_courante.pk,
        )
        with self.assertRaises(ValidationError) as ctx:
            MouvementCaisseService.update(
                form=form,
                user=self.user,
            )
        self.assertIn("clôturée", str(ctx.exception))
        mouvement.refresh_from_db()
        self.assertEqual(mouvement.montant, Decimal("100.00"))
        mock_snapshot.rebuild_day.assert_not_called()

    def test_delete_caisse_fermee_raise_validation_error(self, mock_snapshot, mock_fonds):
        """Caisse fermée : delete lève ValidationError."""
        caisse_courante = self._create_caisse_courante(est_ouverte=True)
        mouvement = MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="ENTREE",
            rubrique=self.rubrique,
            montant=Decimal("50.00"),
            motif="À supprimer",
            effectue_par=self.user,
        )
        caisse_courante.est_ouverte = False
        caisse_courante.save()
        with self.assertRaises(ValidationError) as ctx:
            MouvementCaisseService.delete(mouvement=mouvement)
        self.assertIn("clôturée", str(ctx.exception))
        self.assertTrue(MouvementCaisse.objects.filter(pk=mouvement.pk).exists())
        mock_snapshot.rebuild_day.assert_not_called()

    def test_delete_caisse_ouverte_succes(self, mock_snapshot, mock_fonds):
        """Caisse ouverte : delete supprime le mouvement."""
        caisse_courante = self._create_caisse_courante(est_ouverte=True)
        mouvement = MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="SORTIE",
            rubrique=self.rubrique,
            montant=Decimal("25.00"),
            motif="Supprimé",
            effectue_par=self.user,
        )
        MouvementCaisseService.delete(mouvement=mouvement)
        self.assertFalse(MouvementCaisse.objects.filter(pk=mouvement.pk).exists())
        mock_snapshot.rebuild_day.assert_called()

    def test_create_transfert_cree_un_miroir_unique(self, mock_snapshot, mock_fonds):
        caisse_source = self._create_caisse_courante(est_ouverte=True)
        caisse_destination = self._create_caisse_destination_courante(est_ouverte=True)
        form = CaisseForm(
            self._transfer_form_data(),
            caisse_pk=caisse_source.pk,
        )
        mouvement = MouvementCaisseService.create(
            skip_rebuild=True,
            form=form,
            caisse_courante=caisse_source,
            user=self.user,
            caisse_destination_id=self.caisse_destination.pk,
        )
        miroir = MouvementCaisse.objects.get(mouvement_transfert_source=mouvement)
        self.assertEqual(mouvement.caisse_destination, self.caisse_destination)
        self.assertEqual(miroir.caisse, caisse_destination)
        self.assertEqual(miroir.type_mouvement, "ENTREE")
        self.assertEqual(miroir.montant, Decimal("75.00"))
        self.assertEqual(MouvementCaisse.objects.filter(mouvement_transfert_source=mouvement).count(), 1)
        mock_snapshot.rebuild_day.assert_not_called()
        mock_fonds.rebuild.assert_not_called()

    def test_update_transfert_met_a_jour_le_miroir_sans_duplication(self, mock_snapshot, mock_fonds):
        caisse_source = self._create_caisse_courante(est_ouverte=True)
        self._create_caisse_destination_courante(est_ouverte=True)
        caisse_destination_2 = self._create_caisse_destination_courante(
            caisse=self.caisse_destination_bis,
            est_ouverte=True,
        )
        create_form = CaisseForm(
            self._transfer_form_data(),
            caisse_pk=caisse_source.pk,
        )
        mouvement = MouvementCaisseService.create(
            skip_rebuild=True,
            form=create_form,
            caisse_courante=caisse_source,
            user=self.user,
            caisse_destination_id=self.caisse_destination.pk,
        )
        miroir_initial = MouvementCaisse.objects.get(mouvement_transfert_source=mouvement)
        update_form = CaisseForm(
            self._transfer_form_data(montant="120.00", motif="Transfert modifié"),
            instance=mouvement,
            caisse_pk=caisse_source.pk,
        )
        mouvement = MouvementCaisseService.update(
            skip_rebuild=True,
            form=update_form,
            user=self.user,
            caisse_destination_id=self.caisse_destination_bis.pk,
        )
        miroir_initial.refresh_from_db()
        self.assertEqual(miroir_initial.pk, MouvementCaisse.objects.get(mouvement_transfert_source=mouvement).pk)
        self.assertEqual(miroir_initial.caisse, caisse_destination_2)
        self.assertEqual(miroir_initial.montant, Decimal("120.00"))
        self.assertEqual(miroir_initial.motif, "Transfert modifié")
        self.assertEqual(MouvementCaisse.objects.filter(mouvement_transfert_source=mouvement).count(), 1)

    def test_delete_transfert_supprime_aussi_le_miroir(self, mock_snapshot, mock_fonds):
        caisse_source = self._create_caisse_courante(est_ouverte=True)
        self._create_caisse_destination_courante(est_ouverte=True)
        form = CaisseForm(
            self._transfer_form_data(),
            caisse_pk=caisse_source.pk,
        )
        mouvement = MouvementCaisseService.create(
            skip_rebuild=True,
            form=form,
            caisse_courante=caisse_source,
            user=self.user,
            caisse_destination_id=self.caisse_destination.pk,
        )
        miroir_pk = MouvementCaisse.objects.get(mouvement_transfert_source=mouvement).pk
        MouvementCaisseService.delete(mouvement=mouvement)
        self.assertFalse(MouvementCaisse.objects.filter(pk=mouvement.pk).exists())
        self.assertFalse(MouvementCaisse.objects.filter(pk=miroir_pk).exists())

    def test_delete_miroir_directement_est_interdit(self, mock_snapshot, mock_fonds):
        caisse_source = self._create_caisse_courante(est_ouverte=True)
        self._create_caisse_destination_courante(est_ouverte=True)
        form = CaisseForm(
            self._transfer_form_data(),
            caisse_pk=caisse_source.pk,
        )
        mouvement = MouvementCaisseService.create(
            skip_rebuild=True,
            form=form,
            caisse_courante=caisse_source,
            user=self.user,
            caisse_destination_id=self.caisse_destination.pk,
        )
        miroir = MouvementCaisse.objects.get(mouvement_transfert_source=mouvement)
        with self.assertRaises(ValidationError) as ctx:
            MouvementCaisseService.delete(mouvement=miroir)
        self.assertIn("miroir", str(ctx.exception))


class CaisseClotureIntegrationTestCase(TestCase):
    """Tests d'intégration : scénario fin de journée, caisse clôturée (Phase 4)."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            force_password_change=False,
        )
        self.caisse = Caisse.objects.create(nom="Caisse Test", is_principal=True)
        self.rubrique = RubriqueCaisse.objects.create(
            nom="Divers",
            description="Rubrique test",
            visible=True,
        )
        self.caisse_courante = CaisseCourante.objects.create(
            caisse=self.caisse,
            solde_initial=Decimal("1000.00"),
            est_ouverte=False,
        )

    def test_post_add_mouvement_caisse_fermee_retourne_400(self):
        """POST ajout sur caisse fermée → 400, aucun mouvement créé."""
        self.client.login(username="testuser", password="testpass123")
        get_resp = self.client.get(f"/caisse/{self.caisse_courante.pk}")
        csrf_token = self.client.cookies.get("csrftoken", "")
        csrf_token = csrf_token.value if csrf_token else ""
        count_before = MouvementCaisse.objects.count()
        response = self.client.post(
            f"/caisse/{self.caisse_courante.pk}",
            data={
                "form_type": "add",
                "type_mouvement": "ENTREE",
                "rubrique": str(self.rubrique.pk),
                "montant": "50.00",
                "motif": "Test",
                "csrfmiddlewaretoken": csrf_token,
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(MouvementCaisse.objects.count(), count_before)
        self.assertIn("clôturée", response.content.decode())


class OuvertureCaisseViewTestCase(TestCase):
    def test_solde_initial_retourne_zero_si_dernier_solde_final_est_null(self):
        caisse = Caisse.objects.create(nom="Caisse Ouverture", is_principal=True)
        CaisseCourante.objects.create(
            caisse=caisse,
            solde_initial=Decimal("100.00"),
            solde_final=None,
            est_ouverte=False,
        )
        view = OuvertureCaisseView()
        view.get_caisse = lambda: caisse
        self.assertEqual(view.solde_initial(), Decimal("0"))


class CaisseFormRubriqueHtmxTestCase(TestCase):
    """Régression : hx-get rubrique doit cibler rubrique_champ par pk CaisseCourante."""

    def test_rubrique_hx_get_utilise_pk_caisse_courante(self) -> None:
        caisse = Caisse.objects.create(nom="Caisse HTMX", is_principal=True)
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse,
            solde_initial=Decimal("100.00"),
            est_ouverte=True,
        )
        form = CaisseForm(caisse_pk=caisse_courante.pk)
        attendu = reverse(
            "rubrique_champ",
            kwargs={"caisse_pk": caisse_courante.pk},
        )
        self.assertEqual(form.fields["rubrique"].widget.attrs["hx-get"], attendu)


class RubriqueChampViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="rubrique_test",
            password="testpass123",
            force_password_change=False,
        )
        self.caisse = Caisse.objects.create(
            nom="Caisse Rubrique",
            is_principal=True,
        )
        self.caisse_courante = CaisseCourante.objects.create(
            caisse=self.caisse,
            solde_initial=Decimal("1000.00"),
            est_ouverte=True,
        )

    @patch("caisse.views.assert_caisse_write_access")
    def test_rubrique_transport_reste_sur_le_champ_agent(self, mock_assert_access):
        rubrique_transport = RubriqueCaisse.objects.create(
            nom="Transport",
            description="Rubrique transport",
            visible=True,
            classification_metier=RubriqueCaisse.ClassificationMetier.CHARGE_EXPLOITATION,
        )
        request = self.factory.get(
            "/caisse/rubrique-champ/",
            {"rubrique": rubrique_transport.pk},
        )
        request.user = self.user
        response = rubrique_champ_view(request, caisse_pk=self.caisse_courante.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="agent"', response.content.decode())


class GetTotalVentesCaisseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="caissier_test",
            password="testpass123",
            force_password_change=False,
        )
        self.principal = Caisse.objects.create(
            nom="Caisse Principale",
            is_principal=True,
        )
        self.secondaire = Caisse.objects.create(
            nom="Caisse Secondaire",
            is_principal=False,
        )

    def _create_caisse_courante(self, *, caisse, date_ouverture):
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse,
            ouvert_par=self.user,
            solde_initial=Decimal("1000.00"),
            est_ouverte=True,
        )
        CaisseCourante.objects.filter(pk=caisse_courante.pk).update(
            date_ouverture=date_ouverture
        )
        caisse_courante.refresh_from_db()
        return caisse_courante

    def test_get_total_ventes_caisse_exclut_facture_client(self):
        date_ouverture = timezone.now().replace(
            hour=8, minute=0, second=0, microsecond=0,
        )
        caisse_courante = self._create_caisse_courante(
            caisse=self.principal, date_ouverture=date_ouverture,
        )
        date_vente = date_ouverture.date()
        facture_comptoir = FactureFactory(
            cree_par=self.user, date_facture=date_vente,
            client_comptoir="Client comptoir", valide=True,
        )
        DetailsFactureFactory(facture=facture_comptoir, qte=2, prix=Decimal("100.00"))
        facture_client = FactureFactory(
            cree_par=self.user, date_facture=date_vente, valide=True,
        )
        DetailsFactureFactory(facture=facture_client, qte=3, prix=Decimal("100.00"))
        FactureClientFactory(facture=facture_client, client=ClientFactory())
        facture_non_validee = FactureFactory(
            cree_par=self.user, date_facture=date_vente,
            client_comptoir="Brouillon", valide=False,
        )
        DetailsFactureFactory(facture=facture_non_validee, qte=5, prix=Decimal("100.00"))
        facture_autre_jour = FactureFactory(
            cree_par=self.user,
            date_facture=date_vente - datetime.timedelta(days=1),
            client_comptoir="Autre jour", valide=True,
        )
        DetailsFactureFactory(facture=facture_autre_jour, qte=7, prix=Decimal("100.00"))
        total = get_total_ventes_caisse(caisse_courante=caisse_courante)
        self.assertEqual(total, Decimal("200.00"))

    def test_get_total_ventes_caisse_retourne_zero_hors_caisse_principale(self):
        caisse_courante = self._create_caisse_courante(
            caisse=self.secondaire, date_ouverture=timezone.now(),
        )
        facture = FactureFactory(
            cree_par=self.user,
            date_facture=caisse_courante.date_ouverture.date(),
            client_comptoir="Client comptoir", valide=True,
        )
        DetailsFactureFactory(facture=facture, qte=2, prix=Decimal("100.00"))
        total = get_total_ventes_caisse(caisse_courante=caisse_courante)
        self.assertEqual(total, Decimal("0"))
