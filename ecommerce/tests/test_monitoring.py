"""
Tests pour le module de monitoring e-commerce.

Tests couverts:
- Logs structurés (format JSON)
- Alertes email (seuils critiques)
- Métriques de performance
- Health check
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta
from io import StringIO

from django.utils import timezone
from django.conf import settings

from ecommerce.models import EcommerceLog
from ecommerce.monitoring import (
    MonitoringService,
    StructuredLog,
    ALERT_THRESHOLDS,
)


class TestStructuredLog:
    """Tests pour les logs structurés."""

    def test_to_json_contains_all_fields(self):
        """Le JSON contient tous les champs requis."""
        log = StructuredLog(
            timestamp='2026-06-29T20:00:00',
            level='ERROR',
            module='ecommerce',
            event='sync_article',
            message='Erreur de synchronisation',
            duration_ms=1500,
            article_code='1001',
            commande_id='CMD001',
            success=False,
            error='Connection timeout',
            metadata={'retry_count': 3},
        )

        json_str = log.to_json()
        data = json.loads(json_str)

        assert data['timestamp'] == '2026-06-29T20:00:00'
        assert data['level'] == 'ERROR'
        assert data['event'] == 'sync_article'
        assert data['duration_ms'] == 1500
        assert data['article_code'] == '1001'
        assert data['success'] is False
        assert data['error'] == 'Connection timeout'
        assert data['metadata']['retry_count'] == 3

    def test_to_json_minimal(self):
        """Log minimal sans champs optionnels."""
        log = StructuredLog(
            timestamp='2026-06-29T20:00:00',
            level='INFO',
            module='ecommerce',
            event='test',
            message='Test log',
        )

        json_str = log.to_json()
        data = json.loads(json_str)

        assert data['duration_ms'] is None
        assert data['article_code'] is None
        assert data['metadata'] == {}

    def test_to_dict(self):
        """La conversion en dict fonctionne."""
        log = StructuredLog(
            timestamp='2026-06-29T20:00:00',
            level='INFO',
            module='ecommerce',
            event='test',
            message='Test',
        )

        d = log.to_dict()
        assert isinstance(d, dict)
        assert d['event'] == 'test'


class TestMonitoringService:
    """Tests pour le MonitoringService."""

    @pytest.mark.django_db
    def test_log_event_creates_ecommerce_log(self):
        """log_event() crée une entrée EcommerceLog pour les erreurs."""
        MonitoringService.log_event(
            event='sync_article',
            message='Erreur test',
            level='ERROR',
            article_code='1001',
            success=False,
        )

        logs = EcommerceLog.objects.filter(evenement='sync_article')
        assert logs.count() == 1
        assert logs[0].success is False
        assert logs[0].article_code == '1001'

    @pytest.mark.django_db
    def test_log_event_info_does_not_create_log(self):
        """log_event() INFO ne crée pas d'entrée EcommerceLog."""
        MonitoringService.log_event(
            event='test_event',
            message='Test info',
            level='INFO',
        )

        logs = EcommerceLog.objects.filter(evenement='test_event')
        assert logs.count() == 0

    @pytest.mark.django_db
    def test_check_health_returns_dict(self):
        """check_health() retourne un dict avec status."""
        health = MonitoringService.check_health()

        assert isinstance(health, dict)
        assert 'status' in health
        assert 'timestamp' in health
        assert 'checks' in health

    @pytest.mark.django_db
    def test_check_health_healthy_by_default(self):
        """check_health() est healthy par défaut."""
        health = MonitoringService.check_health()
        assert health['status'] == 'healthy'

    @pytest.mark.django_db
    def test_get_metrics_empty(self):
        """get_metrics() retourne 0 quand aucun log."""
        metrics = MonitoringService.get_metrics(hours=24)

        assert metrics['total_events'] == 0
        assert metrics['success_rate'] == 100.0

    @pytest.mark.django_db
    def test_get_metrics_with_data(self):
        """get_metrics() calcule correctement les métriques."""
        # Créer des logs
        EcommerceLog.objects.create(
            evenement='sync_article',
            success=True,
            message='Sync OK',
            duree_ms=100,
        )
        EcommerceLog.objects.create(
            evenement='sync_article',
            success=False,
            message='Sync error',
            duree_ms=200,
        )
        EcommerceLog.objects.create(
            evenement='import_commande',
            success=True,
            message='Import OK',
            duree_ms=50,
        )

        metrics = MonitoringService.get_metrics(hours=24)

        assert metrics['total_events'] == 3
        assert metrics['errors'] == 1
        assert metrics['success_rate'] == 66.67  # 2/3
        assert metrics['avg_duration_ms'] == 116.67  # (100+200+50)/3
        assert metrics['events_by_type']['sync_article'] == 2
        assert metrics['events_by_type']['import_commande'] == 1
        assert metrics['errors_by_type']['sync_article'] == 1

    @patch('ecommerce.monitoring.send_mail')
    @pytest.mark.django_db
    def test_send_alert_no_admins(self, mock_send_mail):
        """send_alert() retourne False si pas d'admins configurés."""
        # Sauvegarder et vider ADMINS
        old_admins = getattr(settings, 'ADMINS', [])
        settings.ADMINS = []

        result = MonitoringService.send_alert(
            subject='Test',
            message='Test message',
        )

        assert result is False
        mock_send_mail.assert_not_called()

        # Restaurer
        settings.ADMINS = old_admins

    @patch('ecommerce.monitoring.send_mail')
    @pytest.mark.django_db
    def test_send_alert_cooldown(self, mock_send_mail):
        """send_alert() respecte le cooldown (pas de doublon)."""
        # Simuler un envoi récent
        from ecommerce.monitoring import _alert_state
        from datetime import datetime
        _alert_state['WARNING:Test'] = timezone.now()

        result = MonitoringService.send_alert(
            subject='Test',
            message='Test message',
        )

        assert result is False
        mock_send_mail.assert_not_called()

    @pytest.mark.django_db
    def test_log_event_with_metadata(self):
        """log_event() avec métadonnées supplémentaires."""
        MonitoringService.log_event(
            event='sync_article',
            message='Test avec metadata',
            level='ERROR',
            metadata={'retry_count': 3, 'batch_size': 50},
        )

        logs = EcommerceLog.objects.filter(evenement='sync_article')
        assert logs.count() == 1
        assert 'Test avec metadata' in logs[0].message

    @pytest.mark.django_db
    def test_get_metrics_errors_by_type(self):
        """get_metrics() groupe les erreurs par type."""
        EcommerceLog.objects.create(
            evenement='sync_article',
            success=False,
            message='Erreur 1',
        )
        EcommerceLog.objects.create(
            evenement='sync_article',
            success=False,
            message='Erreur 2',
        )
        EcommerceLog.objects.create(
            evenement='import_commande',
            success=False,
            message='Erreur 3',
        )

        metrics = MonitoringService.get_metrics(hours=24)

        assert metrics['errors_by_type']['sync_article'] == 2
        assert metrics['errors_by_type']['import_commande'] == 1
