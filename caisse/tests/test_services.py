"""
caisse/tests/test_services.py

Tests unitaires pour MouvementCaisseService.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from caisse.models import (
    Caisse,
    CaisseCourante,
    MouvementCaisse,
    RubriqueCaisse,
    SousRubriqueCaisse,
)
from caisse.services.mouvement_caisse import MouvementCaisseService
from users.models import CustomUser


class MouvementCaisseServiceTestCase(TestCase):
    """Tests unitaires pour MouvementCaisseService."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpass123",
            force_password_change=False,
        )
        self.caisse = Caisse.objects.create(nom="Caisse Source", is_principal=True)
        self.caisse_destination = Caisse.objects.create(
            nom="Caisse Destination", is_principal=False
        )
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

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_create_caisse_ouverte_succes(self, mock_fonds, mock_snapshot):
        """Caisse ouverte : create crée un mouvement."""
        from caisse.forms import CaisseForm

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

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_create_caisse_fermee_raise_validation_error(self, mock_fonds, mock_snapshot):
        """Caisse fermée : create lève ValidationError."""
        from caisse.forms import CaisseForm

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

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_update_caisse_fermee_raise_validation_error(self, mock_fonds, mock_snapshot):
        """Caisse fermée : update lève ValidationError."""
        from caisse.forms import CaisseForm

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

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_delete_caisse_fermee_raise_validation_error(self, mock_fonds, mock_snapshot):
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

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_delete_caisse_ouverte_succes(self, mock_fonds, mock_snapshot):
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

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_create_transfert_cree_un_miroir_unique(self, mock_fonds, mock_snapshot):
        """Transfert : create crée un mouvement miroir unique."""
        from caisse.forms import CaisseForm

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
        self.assertEqual(
            MouvementCaisse.objects.filter(mouvement_transfert_source=mouvement).count(),
            1,
        )
        mock_snapshot.rebuild_day.assert_not_called()
        mock_fonds.rebuild.assert_not_called()

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_update_transfert_met_a_jour_le_miroir_sans_duplication(
        self, mock_fonds, mock_snapshot
    ):
        """Transfert : update met à jour le miroir sans duplication."""
        from caisse.forms import CaisseForm

        caisse_source = self._create_caisse_courante(est_ouverte=True)
        self._create_caisse_destination_courante(est_ouverte=True)
        caisse_destination_2 = self._create_caisse_destination_courante(
            caisse=self.caisse_destination,
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
            caisse_destination_id=self.caisse_destination.pk,
        )

        miroir_initial.refresh_from_db()
        self.assertEqual(
            miroir_initial.pk,
            MouvementCaisse.objects.get(mouvement_transfert_source=mouvement).pk,
        )
        self.assertEqual(miroir_initial.montant, Decimal("120.00"))
        self.assertEqual(miroir_initial.motif, "Transfert modifié")
        self.assertEqual(
            MouvementCaisse.objects.filter(mouvement_transfert_source=mouvement).count(),
            1,
        )

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_delete_transfert_supprime_aussi_le_miroir(self, mock_fonds, mock_snapshot):
        """Transfert : delete supprime aussi le miroir."""
        from caisse.forms import CaisseForm

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

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_delete_miroir_directement_est_interdit(self, mock_fonds, mock_snapshot):
        """Miroir : delete direct lève ValidationError."""
        from caisse.forms import CaisseForm

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

    @patch("caisse.services.mouvement_caisse.SnapshotService")
    @patch("caisse.services.mouvement_caisse.FondsRoulementService")
    def test_sortie_solde_insuffisant_raise_validation_error(self, mock_fonds, mock_snapshot):
        """Règle métier : sortie avec solde insuffisant lève ValidationError."""
        from caisse.forms import CaisseForm

        caisse_courante = self._create_caisse_courante(est_ouverte=True)
        # Créer une entrée de 100
        MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="ENTREE",
            rubrique=self.rubrique,
            montant=Decimal("100.00"),
            motif="Entrée initiale",
            effectue_par=self.user,
        )

        # Tentative de sortie de 2000 (solde = 1000 initial + 100 entrée = 1100, KO)
        form = CaisseForm(
            {
                "type_mouvement": "SORTIE",
                "rubrique": str(self.rubrique.pk),
                "montant": "2000.00",
                "motif": "Sortie trop importante",
            },
            caisse_pk=caisse_courante.pk,
        )

        with self.assertRaises(ValidationError) as ctx:
            MouvementCaisseService.create(
                form=form,
                caisse_courante=caisse_courante,
                user=self.user,
                skip_rebuild=True,
            )

        self.assertIn("excède", str(ctx.exception))
        self.assertEqual(MouvementCaisse.objects.count(), 1)

    def test_total_par_type_caisse(self):
        """Calcul du total par type de mouvement."""
        caisse_courante = self._create_caisse_courante(est_ouverte=True)
        MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="ENTREE",
            rubrique=self.rubrique,
            montant=Decimal("100.00"),
            motif="Entrée 1",
            effectue_par=self.user,
        )
        MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="ENTREE",
            rubrique=self.rubrique,
            montant=Decimal("200.00"),
            motif="Entrée 2",
            effectue_par=self.user,
        )
        MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="SORTIE",
            rubrique=self.rubrique,
            montant=Decimal("50.00"),
            motif="Sortie 1",
            effectue_par=self.user,
        )

        total_entrees = MouvementCaisseService.total_par_type(caisse_courante, "ENTREE")
        total_sorties = MouvementCaisseService.total_par_type(caisse_courante, "SORTIE")

        self.assertEqual(total_entrees, Decimal("300.00"))
        self.assertEqual(total_sorties, Decimal("50.00"))

    def test_assert_caisse_ouverte_fermee_raise(self):
        """_assert_caisse_ouverte lève ValidationError si caisse fermée."""
        caisse_courante = self._create_caisse_courante(est_ouverte=False)

        with self.assertRaises(ValidationError) as ctx:
            MouvementCaisseService._assert_caisse_ouverte(caisse_courante)

        self.assertIn("clôturée", str(ctx.exception))

    def test_assert_caisse_ouverte_ouverte_ok(self):
        """_assert_caisse_ouverte ne lève pas d'erreur si caisse ouverte."""
        caisse_courante = self._create_caisse_courante(est_ouverte=True)
        # Ne doit pas lever d'exception
        MouvementCaisseService._assert_caisse_ouverte(caisse_courante)

    def test_assert_solde_suffisant_suffisant_ok(self):
        """_assert_solde_suffisant ne lève pas si solde suffisant."""
        caisse_courante = self._create_caisse_courante(est_ouverte=True)
        # Solde initial = 1000, pas de sorties, donc solde disponible = 1000
        MouvementCaisseService._assert_solde_suffisant(caisse_courante, Decimal("500.00"))

    def test_assert_solde_suffisant_insuffisant_raise(self):
        """_assert_solde_suffisant lève ValidationError si solde insuffisant."""
        caisse_courante = self._create_caisse_courante(est_ouverte=True)
        # Solde disponible = 1000, tentative de sortie de 1500
        with self.assertRaises(ValidationError) as ctx:
            MouvementCaisseService._assert_solde_suffisant(
                caisse_courante, Decimal("1500.00")
            )

        self.assertIn("excède", str(ctx.exception))

    def test_is_transfert_true(self):
        """_is_transfert retourne True pour rubrique 'transfert caisse'."""
        mouvement = MouvementCaisse(
            rubrique=self.rubrique_transfert,
            montant=Decimal("100.00"),
        )
        self.assertTrue(MouvementCaisseService._is_transfert(mouvement))

    def test_is_transfert_false(self):
        """_is_transfert retourne False pour autre rubrique."""
        mouvement = MouvementCaisse(
            rubrique=self.rubrique,
            montant=Decimal("100.00"),
        )
        self.assertFalse(MouvementCaisseService._is_transfert(mouvement))

    def test_assert_not_mirror_raise(self):
        """_assert_not_mirror lève ValidationError pour un miroir."""
        mouvement = MouvementCaisse(
            rubrique=self.rubrique,
            montant=Decimal("100.00"),
            mouvement_transfert_source_id=1,
        )
        with self.assertRaises(ValidationError) as ctx:
            MouvementCaisseService._assert_not_mirror(mouvement)

        self.assertIn("miroir", str(ctx.exception))

    def test_assert_not_mirror_ok(self):
        """_assert_not_mirror ne lève pas pour un mouvement normal."""
        mouvement = MouvementCaisse(
            rubrique=self.rubrique,
            montant=Decimal("100.00"),
        )
        # Ne doit pas lever d'exception
        MouvementCaisseService._assert_not_mirror(mouvement)
