"""
caisse/tests/test_models.py

Tests pour les modèles de caisse.
"""

from decimal import Decimal
from django.test import TestCase

from caisse.models import Caisse, CaisseCourante, MouvementCaisse, RubriqueCaisse, SousRubriqueCaisse
from users.models import CustomUser


class CaisseModelTestCase(TestCase):
    """Tests pour les modèles de caisse."""

    def test_caisse_str(self):
        """Test de __str__ de Caisse."""
        caisse = Caisse.objects.create(nom="Caisse Principale", is_principal=True)
        self.assertEqual(str(caisse), "Caisse Principale")

    def test_caisse_courante_str(self):
        """Test de __str__ de CaisseCourante."""
        caisse = Caisse.objects.create(nom="Caisse Test")
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse,
            solde_initial=Decimal("1000.00"),
        )
        expected = f"Caisse #{caisse_courante.id} - {caisse_courante.date_ouverture.date()}"
        self.assertEqual(str(caisse_courante), expected)

    def test_caisse_courante_save_sets_taux_ouverture(self):
        """Test que save() calcule automatiquement taux_ouverture et solde_initial_usd."""
        from parametres.models import get_taux_usd_cdf
        caisse = Caisse.objects.create(nom="Caisse Test", is_principal=True)
        
        # Créer une caisse courante avec solde initial
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse,
            solde_initial=Decimal("1000.00"),
        )
        
        # Vérifier que taux_ouverture et solde_initial_usd ont été calculés
        self.assertIsNotNone(caisse_courante.taux_ouverture)
        self.assertIsNotNone(caisse_courante.solde_initial_usd)
        
        # solde_initial_usd = solde_initial / taux_ouverture
        expected_usd = Decimal("1000.00") / caisse_courante.taux_ouverture
        self.assertEqual(caisse_courante.solde_initial_usd, expected_usd)

    def test_rubrique_caisse_str(self):
        """Test de __str__ de RubriqueCaisse."""
        rubrique = RubriqueCaisse.objects.create(
            nom="Divers",
            description="Rubrique diverse",
        )
        self.assertEqual(str(rubrique), "Divers")

    def test_mouvement_caisse_str(self):
        """Test de __str__ de MouvementCaisse."""
        caisse = Caisse.objects.create(nom="Caisse Test")
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse,
            solde_initial=Decimal("1000.00"),
        )
        rubrique = RubriqueCaisse.objects.create(nom="Divers")
        user = CustomUser.objects.create_user(username="testuser")
        
        mouvement = MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="ENTREE",
            rubrique=rubrique,
            montant=Decimal("50.00"),
            motif="Test",
            effectue_par=user,
        )
        expected = "ENTREE - 50.00"
        self.assertEqual(str(mouvement), expected)

    def test_mouvement_caisse_badge_entite_with_caisse_destination(self):
        """Test de badge_entite avec caisse_destination."""
        caisse1 = Caisse.objects.create(nom="Caisse Source")
        caisse2 = Caisse.objects.create(nom="Caisse Destination")
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse1,
            solde_initial=Decimal("1000.00"),
        )
        rubrique = RubriqueCaisse.objects.create(nom="Transfert caisse")
        user = CustomUser.objects.create_user(username="testuser")
        
        mouvement = MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="SORTIE",
            rubrique=rubrique,
            montant=Decimal("100.00"),
            motif="Transfert",
            effectue_par=user,
            caisse_destination=caisse2,
        )
        
        self.assertEqual(mouvement.badge_entite, "Caisse Destination")

    def test_mouvement_caisse_badge_entite_with_sous_rubrique(self):
        """Test de badge_entite avec sous_rubrique."""
        caisse = Caisse.objects.create(nom="Caisse Test")
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse,
            solde_initial=Decimal("1000.00"),
        )
        rubrique = RubriqueCaisse.objects.create(nom="Divers")
        sous_rubrique = SousRubriqueCaisse.objects.create(nom="Sous-rubrique Test", rubrique=rubrique)
        user = CustomUser.objects.create_user(username="testuser")
        
        mouvement = MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="SORTIE",
            rubrique=rubrique,
            sous_rubrique=sous_rubrique,
            montant=Decimal("50.00"),
            motif="Test",
            effectue_par=user,
        )
        
        self.assertEqual(mouvement.badge_entite, "Sous-rubrique Test")

    def test_mouvement_caisse_save_sets_montant_usd(self):
        """Test que save() calcule automatiquement montant_usd."""
        from parametres.models import get_taux_usd_cdf
        caisse = Caisse.objects.create(nom="Caisse Test")
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse,
            solde_initial=Decimal("1000.00"),
        )
        rubrique = RubriqueCaisse.objects.create(nom="Divers")
        user = CustomUser.objects.create_user(username="testuser")
        
        mouvement = MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="ENTREE",
            rubrique=rubrique,
            montant=Decimal("100.00"),
            motif="Test",
            effectue_par=user,
        )
        
        # Vérifier que montant_usd et taux_mouvement ont été calculés
        self.assertIsNotNone(mouvement.taux_mouvement)
        self.assertIsNotNone(mouvement.montant_usd)
        
        # montant_usd = montant / taux_mouvement
        expected_usd = Decimal("100.00") / mouvement.taux_mouvement
        self.assertEqual(mouvement.montant_usd, expected_usd)

    def test_mouvement_caisse_save_preserves_montant_usd_on_update(self):
        """Test que save() préserve montant_usd lors des modifications."""
        caisse = Caisse.objects.create(nom="Caisse Test")
        caisse_courante = CaisseCourante.objects.create(
            caisse=caisse,
            solde_initial=Decimal("1000.00"),
        )
        rubrique = RubriqueCaisse.objects.create(nom="Divers")
        user = CustomUser.objects.create_user(username="testuser")
        
        mouvement = MouvementCaisse.objects.create(
            caisse=caisse_courante,
            type_mouvement="ENTREE",
            rubrique=rubrique,
            montant=Decimal("100.00"),
            motif="Test",
            effectue_par=user,
        )
        
        original_montant_usd = mouvement.montant_usd
        original_taux = mouvement.taux_mouvement
        
        # Modifier le motif
        mouvement.motif = "Modifié"
        mouvement.save()
        
        # Vérifier que montant_usd et taux_mouvement n'ont pas changé
        mouvement.refresh_from_db()
        self.assertEqual(mouvement.montant_usd, original_montant_usd)
        self.assertEqual(mouvement.taux_mouvement, original_taux)
