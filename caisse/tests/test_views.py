"""
caisse/tests/test_views.py

Tests pour les vues et formulaires de la caisse.
"""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from caisse.forms import CaisseForm, OuvertureCaisseValidateForm, ClotureCaisseValidateForm
from caisse.models import Caisse, CaisseCourante, MouvementCaisse, RubriqueCaisse, SousRubriqueCaisse

User = get_user_model()


class CaisseFormTestCase(TestCase):
    """Tests pour le formulaire CaisseForm."""

    def setUp(self):
        self.caisse = Caisse.objects.create(nom="Caisse Test", is_principal=True)
        self.caisse_courante = CaisseCourante.objects.create(
            caisse=self.caisse,
            solde_initial=Decimal("1000.00"),
            est_ouverte=True,
        )
        self.rubrique = RubriqueCaisse.objects.create(
            nom="Divers", description="Test", visible=True,
        )

    def test_caisse_form_valide(self):
        """CaisseForm valide avec des données correctes."""
        form = CaisseForm(
            data={
                "type_mouvement": "ENTREE",
                "rubrique": str(self.rubrique.pk),
                "montant": "50.00",
                "motif": "Test motif",
            },
            caisse_pk=self.caisse_courante.pk,
        )
        self.assertTrue(form.is_valid())

    def test_caisse_form_motif_obligatoire(self):
        """CaisseForm : motif est obligatoire."""
        form = CaisseForm(
            data={
                "type_mouvement": "ENTREE",
                "rubrique": str(self.rubrique.pk),
                "montant": "50.00",
                "motif": "",
            },
            caisse_pk=self.caisse_courante.pk,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("motif", form.errors)

    def test_caisse_form_montant_invalide(self):
        """CaisseForm : montant invalide."""
        form = CaisseForm(
            data={
                "type_mouvement": "ENTREE",
                "rubrique": str(self.rubrique.pk),
                "montant": "abc",
                "motif": "Test",
            },
            caisse_pk=self.caisse_courante.pk,
        )
        self.assertFalse(form.is_valid())

    def test_caisse_form_instance_edition(self):
        """CaisseForm en mode édition : le champ rubrique a un trigger change."""
        mouvement = MouvementCaisse.objects.create(
            caisse=self.caisse_courante,
            type_mouvement="ENTREE",
            rubrique=self.rubrique,
            montant=Decimal("100.00"),
            motif="Test",
            effectue_par=User.objects.create_user(username="testuser"),
        )
        form = CaisseForm(
            instance=mouvement,
            caisse_pk=self.caisse_courante.pk,
        )
        self.assertIn("hx-trigger", form.fields["rubrique"].widget.attrs)
        trigger = form.fields["rubrique"].widget.attrs["hx-trigger"]
        self.assertEqual(trigger, "change")

    def test_caisse_form_sans_instance(self):
        """CaisseForm en mode création : le champ rubrique a un trigger load, change."""
        form = CaisseForm(caisse_pk=self.caisse_courante.pk)
        self.assertIn("hx-trigger", form.fields["rubrique"].widget.attrs)
        trigger = form.fields["rubrique"].widget.attrs["hx-trigger"]
        self.assertEqual(trigger, "load, change")


class OuvertureCaisseValidateFormTestCase(TestCase):
    """Tests pour OuvertureCaisseValidateForm."""

    def test_form_is_valid(self):
        """OuvertureCaisseValidateForm est toujours valide (pas de champs)."""
        form = OuvertureCaisseValidateForm(data={})
        self.assertTrue(form.is_valid())


class ClotureCaisseValidateFormTestCase(TestCase):
    """Tests pour ClotureCaisseValidateForm."""

    def test_form_is_valid(self):
        """ClotureCaisseValidateForm est toujours valide (pas de champs)."""
        form = ClotureCaisseValidateForm(data={})
        self.assertTrue(form.is_valid())


class CaisseModelAdvancedTestCase(TestCase):
    """Tests supplémentaires pour les modèles caisse (modèles avancés)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123",
            force_password_change=False,
        )
        self.caisse = Caisse.objects.create(nom="Caisse Test", is_principal=True)
        self.caisse_courante = CaisseCourante.objects.create(
            caisse=self.caisse, solde_initial=Decimal("1000.00"),
        )
        self.rubrique = RubriqueCaisse.objects.create(nom="Divers", description="Test")

    def test_sous_rubrique_creation(self):
        """Test de création d'une sous-rubrique."""
        rubrique = RubriqueCaisse.objects.create(
            nom="Transport", description="Frais transport", visible=True,
        )
        sous = SousRubriqueCaisse.objects.create(
            rubrique=rubrique,
            nom="Carburant",
            description="Frais de carburant",
        )
        self.assertEqual(str(sous), "Carburant")
        self.assertEqual(sous.rubrique, rubrique)

    def test_mouvement_caisse_badge_default(self):
        """badge_entite retourne None si pas de sous_rubrique ni caisse_destination."""
        mouvement = MouvementCaisse.objects.create(
            caisse=self.caisse_courante,
            type_mouvement="ENTREE",
            rubrique=self.rubrique,
            montant=Decimal("50.00"),
            motif="Test",
            effectue_par=self.user,
        )
        self.assertIsNone(mouvement.badge_entite)

    def test_rubrique_classification_default(self):
        """RubriqueCaisse a une classification par défaut NONE."""
        rubrique = RubriqueCaisse.objects.create(nom="Test", description="Test")
        self.assertEqual(rubrique.classification_metier, "NONE")

    def test_mouvement_caisse_save_preserves_montant_usd(self):
        """save() préserve montant_usd sur mise à jour."""
        mouvement = MouvementCaisse.objects.create(
            caisse=self.caisse_courante,
            type_mouvement="ENTREE",
            rubrique=self.rubrique,
            montant=Decimal("100.00"),
            motif="Test",
            effectue_par=self.user,
        )
        original_usd = mouvement.montant_usd
        original_taux = mouvement.taux_mouvement

        mouvement.motif = "Modifié"
        mouvement.save()
        mouvement.refresh_from_db()

        self.assertEqual(mouvement.montant_usd, original_usd)
        self.assertEqual(mouvement.taux_mouvement, original_taux)
