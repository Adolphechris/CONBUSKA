from decimal import Decimal
from datetime import date

from django.test import TestCase
from django.utils import timezone

from parametres.models import TauxEchange, get_taux_usd_cdf
from parametres.exceptions import RateNotFoundError


class TestTauxEchangeModel(TestCase):
    def setUp(self):
        self.t1 = TauxEchange.objects.create(
            devise_source='USD', devise_cible='CDF',
            taux=Decimal('2500.00'),
            effective_date=date(2024, 1, 1),
        )

    def test_str_representation(self):
        self.assertIn('USD → CDF', str(self.t1))

    def test_get_rate_for_date_returns_valid(self):
        rate = TauxEchange.objects.get_rate_for_date('USD', 'CDF', date(2024, 6, 1))
        self.assertEqual(rate, self.t1)

    def test_get_rate_for_date_raises_not_found(self):
        with self.assertRaises(RateNotFoundError):
            TauxEchange.objects.get_rate_for_date('EUR', 'CDF', date(2024, 6, 1))

    def test_get_taux_usd_cdf_fallback(self):
        # Avec un taux défini
        taux = get_taux_usd_cdf(date(2024, 6, 1))
        self.assertEqual(taux, self.t1.taux)

    def test_get_taux_usd_cdf_default_when_not_found(self):
        taux = get_taux_usd_cdf(date(2023, 1, 1))
        self.assertEqual(taux, Decimal('2500.00'))
