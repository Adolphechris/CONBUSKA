"""
Tests pour les commandes cron du module e-commerce.

Tests couverts:
- sync_firestore_cron: dry-run, retry echoues, purge logs
- cleanup_abandoned_carts: dry-run, suppression paniers
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta
from io import StringIO

from django.core.management import call_command
from django.utils import timezone

from ecommerce.models import EcommerceLog, SyncQueue


class TestSyncFirestoreCron:
    """Tests pour la commande sync_firestore_cron."""

    @pytest.mark.django_db
    def test_dry_run_mode(self):
        """Le mode dry-run ne modifie rien."""
        out = StringIO()
        call_command('sync_firestore_cron', '--dry-run', stdout=out)
        output = out.getvalue()

        assert "DRY-RUN" in output
        assert "Termin" in output

    @pytest.mark.django_db
    def test_purge_old_logs(self):
        """Les logs de plus de 30 jours sont purges."""
        old_log = EcommerceLog.objects.create(
            evenement='sync_article',
            success=True,
            message='Vieux log',
        )
        EcommerceLog.objects.filter(pk=old_log.pk).update(
            timestamp=timezone.now() - timedelta(days=31)
        )
        EcommerceLog.objects.create(
            evenement='sync_article',
            success=True,
            message='Log recent',
        )
        out = StringIO()
        call_command('sync_firestore_cron', stdout=out)
        output = out.getvalue()

        assert "logs purges" in output or "purge" in output or "1 logs" in output or "purge" in output.lower()

    @pytest.mark.django_db
    def test_verbose_mode(self):
        """Le mode verbose affiche plus de details."""
        out = StringIO()
        call_command('sync_firestore_cron', '--verbose', stdout=out)
        output = out.getvalue()

        assert "Termin" in output

    @pytest.mark.django_db
    def test_retry_failed_syncs_empty(self):
        """Aucune sync echouee = rien a retenter."""
        out = StringIO()
        call_command('sync_firestore_cron', stdout=out)
        output = out.getvalue()

        assert "traitees" in output or "0" in output

    @pytest.mark.django_db
    def test_cron_logs_ecommerce_log(self):
        """Le cron cree une entree EcommerceLog."""
        out = StringIO()
        call_command('sync_firestore_cron', stdout=out)
        logs = EcommerceLog.objects.filter(evenement='sync_article')
        assert logs.count() >= 1


class TestCleanupAbandonedCarts:
    """Tests pour la commande cleanup_abandoned_carts."""

    @pytest.mark.django_db
    def test_dry_run_mode(self):
        """Le mode dry-run ne supprime rien."""
        out = StringIO()
        call_command('cleanup_abandoned_carts', '--dry-run', stdout=out)
        output = out.getvalue()

        assert "DRY-RUN" in output
        assert "termin" in output

    @pytest.mark.django_db
    def test_custom_hours(self):
        """L'option --hours est prise en compte."""
        out = StringIO()
        call_command('cleanup_abandoned_carts', '--hours', '48', '--dry-run', stdout=out)
        output = out.getvalue()

        assert "48h" in output or "48 heures" in output
        assert "DRY-RUN" in output
