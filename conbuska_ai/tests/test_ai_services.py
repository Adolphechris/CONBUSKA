from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch, Mock

from django.test import TestCase

from conbuska_ai.services import ConbuskaAIService


class TestConbuskaAIService(TestCase):
    def test_analyser_ventes_empty(self):
        service = ConbuskaAIService()
        result = service.analyser_ventes(periode_jours=7)

        self.assertIn('total_ventes', result)
        self.assertIn('nb_factures', result)
        self.assertEqual(result['nb_factures'], 0)
        self.assertEqual(result['total_ventes'], 0.0)
        self.assertEqual(result['moyenne_par_facture'], 0)

    def test_analyser_stock_empty(self):
        service = ConbuskaAIService()
        result = service.analyser_stock()

        self.assertEqual(result['articles_rupture'], 0)
        self.assertEqual(result['articles_stock_bas'], 0)
        self.assertEqual(result['total_articles'], 0)
        self.assertEqual(result['valeur_stock'], 0.0)

    def test_analyser_paie_no_bulletins(self):
        service = ConbuskaAIService()
        mois = date.today().replace(day=1)
        result = service.analyser_paie(mois=mois)

        self.assertEqual(result['nb_bulletins'], 0)
        self.assertEqual(result['total_salaire_brut'], 0.0)

    def test_generer_rapport_ventes(self):
        service = ConbuskaAIService()
        rapport = service.generer_rapport_automatique('ventes')
        self.assertIn('Rapport des ventes', rapport)
        self.assertIn('Chiffre d\'affaires', rapport)

    def test_generer_rapport_invalide(self):
        service = ConbuskaAIService()
        rapport = service.generer_rapport_automatique('inconnu')
        self.assertEqual(rapport, "Type de rapport non reconnu.")

    def test_chat_sans_api_key(self):
        with patch('conbuska_ai.services.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = None
            service = ConbuskaAIService()
            self.assertIsNone(service.model)
