"""
factures/tests/test_double_devise.py

Tests TDD pour la gestion double devise USD/FC dans les factures.

Critères de validation :
- Montants stockés en USD et FC
- Taux historique enregistré
- Conversion automatique
"""

import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

from factures.models import Facture, DetailsFacture
from factures.tests.factories import (
    FactureFactory,
    DetailsFactureFactory,
    CustomUserFactory,
    ArticleFactory,
)
from parametres.models import TauxEchange, Magasin
from produits.models import Stock


@pytest.mark.django_db
class TestGestionDoubleDevise:
    """Tests pour la gestion double devise USD/FC."""
    
    def setup_method(self):
        """Créer un magasin principal et du stock pour les tests."""
        self.magasin = Magasin.objects.create(
            nom="Magasin Principal",
            description="Magasin principal de test",
            is_principal=True,
            localisation="Test"
        )

    def _creer_stock_article(self, article, qte=100, date_peremption=None):
        """Helper pour créer du stock pour un article."""
        if date_peremption is None:
            date_peremption = datetime.date.today() + datetime.timedelta(days=365)
        
        Stock.objects.create(
            magasin=self.magasin,
            article=article,
            qte=qte,
            date_peremption=date_peremption
        )

    def test_facture_a_champs_devise_et_taux(self):
        """
        Vérifie que les champs devise, taux et valeur_usd existent
        et sont correctement définis.
        """
        facture = FactureFactory(devise='FC', taux=Decimal('2800.00'))
        
        assert hasattr(facture, 'devise')
        assert hasattr(facture, 'taux')
        assert hasattr(facture, 'valeur_usd')
        assert facture.devise == 'FC'
        assert facture.taux == Decimal('2800.00')

    def test_facture_usd_sans_taux(self):
        """
        Une facture en USD peut avoir taux=0 (non utilisé).
        """
        facture = FactureFactory(devise='$', taux=Decimal('0.00'))
        
        assert facture.devise == '$'
        assert facture.taux == Decimal('0.00')

    def test_details_facture_a_champs_valeur_usd_et_taux(self):
        """
        Vérifie que DetailsFacture a les champs valeur_usd et taux_creation.
        """
        detail = DetailsFactureFactory()
        
        assert hasattr(detail, 'valeur_usd')
        assert hasattr(detail, 'taux_creation')

    def test_montants_stockes_en_usd_et_fc_devise_fc(self):
        """
        Pour une facture en FC, les montants sont stockés en FC (prix)
        et convertis en USD (valeur_usd).
        """
        facture = FactureFactory(devise='FC', taux=Decimal('2800.00'))
        detail = DetailsFactureFactory(
            facture=facture,
            qte=2,
            prix=Decimal('1400.00')  # 1400 FC par unité
        )
        
        # Le prix est en FC
        assert detail.prix == Decimal('1400.00')
        
        # La valeur USD est calculée automatiquement
        expected_usd = Decimal('2800.00') / Decimal('2800.00')  # 1.00 USD
        assert detail.valeur_usd == expected_usd

    def test_montants_stockes_en_usd_et_fc_devise_usd(self):
        """
        Pour une facture en USD, les montants sont stockés en USD.
        """
        facture = FactureFactory(devise='$', taux=Decimal('0.00'))
        detail = DetailsFactureFactory(
            facture=facture,
            qte=3,
            prix=Decimal('100.00')  # 100 USD par unité
        )
        
        # Le prix est en USD
        assert detail.prix == Decimal('100.00')
        
        # La valeur USD est identique au montant
        expected_usd = Decimal('300.00')  # 3 * 100
        assert detail.valeur_usd == expected_usd

    def test_taux_historique_enregistre_details_facture(self):
        """
        Le taux de change utilisé au moment de la création est enregistré
        dans DetailsFacture.taux_creation.
        """
        # Créer un taux dans le passé
        date_taux = datetime.date(2024, 1, 15)
        taux_obj = TauxEchange.objects.create(
            devise_source='USD',
            devise_cible='CDF',
            taux=Decimal('2750.00'),
            effective_date=date_taux
        )
        
        facture = FactureFactory(
            devise='FC',
            taux=Decimal('2750.00'),
            date_facture=date_taux
        )
        detail = DetailsFactureFactory(
            facture=facture,
            qte=1,
            prix=Decimal('2750.00')
        )
        
        # Le taux historique est enregistré
        assert detail.taux_creation == Decimal('2750.00')
        assert detail.taux_creation == taux_obj.taux

    def test_taux_recupere_depuis_parametres(self):
        """
        Vérifie que le taux peut être récupéré depuis le modèle TauxEchange.
        """
        # Créer un taux
        taux_value = Decimal('2850.00')
        TauxEchange.objects.create(
            devise_source='USD',
            devise_cible='CDF',
            taux=taux_value,
            effective_date=datetime.date.today()
        )
        
        # Récupérer le taux via le manager
        taux_obj = TauxEchange.objects.get_rate_for_date('USD', 'CDF')
        assert taux_obj.taux == taux_value

    def test_valeur_usd_facture_calculee_automatiquement(self):
        """
        La valeur_usd de la facture est calculée automatiquement lors de la validation.
        """
        facture = FactureFactory(devise='FC', taux=Decimal('2800.00'), valide=False)
        detail = DetailsFactureFactory(
            facture=facture,
            qte=2,
            prix=Decimal('1400.00')
        )
        
        # Créer du stock pour l'article
        self._creer_stock_article(detail.article, qte=10)
        
        # Avant validation, valeur_usd peut être None
        facture.refresh_from_db()
        assert facture.valeur_usd is None or facture.valeur_usd == Decimal('0')
        
        # Après validation, valeur_usd est calculée
        user = CustomUserFactory()
        from factures.services import FactureService
        from clients.models import Client
        
        client = Client.objects.create(
            code=9999,
            nom="Client Test",
            email="test@test.com",
            adresse="Test",
            telephone="0000000000",
            ville="Kinshasa"
        )
        from factures.models import FactureClient
        FactureClient.objects.create(facture=facture, client=client)
        
        FactureService.valider(facture=facture, user=user)
        
        facture.refresh_from_db()
        # total = 2 * 1400 = 2800 FC
        # valeur_usd = 2800 / 2800 = 1.00 USD
        assert facture.valeur_usd == Decimal('1.0000')

    def test_valeur_usd_facture_usd_egal_total(self):
        """
        Pour une facture en USD, valeur_usd = total (pas de conversion).
        """
        facture = FactureFactory(devise='$', taux=Decimal('1.00'), valide=False)
        detail = DetailsFactureFactory(
            facture=facture,
            qte=2,
            prix=Decimal('100.00')
        )
        
        # Créer du stock pour l'article
        self._creer_stock_article(detail.article, qte=10)
        
        user = CustomUserFactory()
        from factures.services import FactureService
        from clients.models import Client
        
        client = Client.objects.create(
            code=9998,
            nom="Client Test 2",
            email="test2@test.com",
            adresse="Test",
            telephone="0000000000",
            ville="Kinshasa"
        )
        from factures.models import FactureClient
        FactureClient.objects.create(facture=facture, client=client)
        
        FactureService.valider(facture=facture, user=user)
        
        facture.refresh_from_db()
        # total = 2 * 100 = 200 USD
        # valeur_usd = 200 USD
        assert facture.valeur_usd == Decimal('200.0000')

    def test_conversion_automatique_affichage_total_devise(self):
        """
        La propriété total_devise effectue la conversion automatique.
        """
        facture = FactureFactory(devise='FC', taux=Decimal('2800.00'))
        detail = DetailsFactureFactory(
            facture=facture,
            qte=1,
            prix=Decimal('5600.00')
        )
        
        # total en FC = 5600
        # total_devise en USD = 5600 / 2800 = 2.00
        expected_usd = Decimal('5600.00') / Decimal('2800.00')
        assert facture.total_devise == expected_usd

    def test_facture_validee_taux_non_modifiable(self):
        """
        Une fois validée, le taux ne peut plus être modifié.
        """
        facture = FactureFactory(devise='FC', taux=Decimal('2800.00'), valide=True)
        
        # Tentative de modification du taux
        facture.taux = Decimal('3000.00')
        
        with pytest.raises(ValidationError) as exc_info:
            facture.full_clean()
        
        assert "taux" in str(exc_info.value).lower()

    def test_facture_validee_devise_non_modifiable(self):
        """
        Une fois validée, la devise ne peut plus être modifiée.
        """
        facture = FactureFactory(devise='FC', taux=Decimal('2800.00'), valide=True)
        
        # Tentative de modification de la devise
        facture.devise = '$'
        
        with pytest.raises(ValidationError) as exc_info:
            facture.full_clean()
        
        assert "devise" in str(exc_info.value).lower()

    def test_validation_facture_necessite_taux_si_fc(self):
        """
        Une facture en FC doit avoir un taux défini pour être validée.
        """
        facture = FactureFactory(devise='FC', taux=Decimal('0.00'), valide=False, client_comptoir="Client Test")
        detail = DetailsFactureFactory(facture=facture)
        
        # Créer du stock pour l'article
        self._creer_stock_article(detail.article, qte=10)
        
        user = CustomUserFactory()
        from factures.services import FactureService
        
        with pytest.raises(ValidationError) as exc_info:
            FactureService.valider(facture=facture, user=user)
        
        assert "taux" in str(exc_info.value).lower()

    def test_coherence_valeur_usd_avec_total_et_taux(self):
        """
        La valeur_usd enregistrée doit être cohérente avec total FC et taux.
        """
        facture = FactureFactory(devise='FC', taux=Decimal('2800.00'), valide=False)
        detail = DetailsFactureFactory(
            facture=facture,
            qte=2,
            prix=Decimal('1400.00')
        )
        
        # Créer du stock pour l'article
        self._creer_stock_article(detail.article, qte=10)
        
        # total = 2800 FC
        # valeur_usd attendue = 2800 / 2800 = 1.00 USD
        expected_usd = Decimal('2800.00') / Decimal('2800.00')
        
        user = CustomUserFactory()
        from factures.services import FactureService
        from clients.models import Client
        
        client = Client.objects.create(
            code=9997,
            nom="Client Test 3",
            email="test3@test.com",
            adresse="Test",
            telephone="0000000000",
            ville="Kinshasa"
        )
        from factures.models import FactureClient
        FactureClient.objects.create(facture=facture, client=client)
        
        FactureService.valider(facture=facture, user=user)
        
        facture.refresh_from_db()
        assert facture.valeur_usd == expected_usd

    def test_details_facture_immutable_apres_creation(self):
        """
        Une fois créée, une ligne de détail conserve sa valeur_usd et taux_creation.
        """
        facture = FactureFactory(devise='FC', taux=Decimal('2800.00'))
        detail = DetailsFactureFactory(
            facture=facture,
            qte=1,
            prix=Decimal('1400.00')
        )
        
        original_valeur_usd = detail.valeur_usd
        original_taux = detail.taux_creation
        
        # Modification du prix (en FC)
        detail.prix = Decimal('1500.00')
        detail.save()
        
        # La valeur_usd et taux_creation restent inchangés
        detail.refresh_from_db()
        assert detail.valeur_usd == original_valeur_usd
        assert detail.taux_creation == original_taux
