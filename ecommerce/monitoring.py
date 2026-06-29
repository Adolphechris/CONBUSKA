"""
Module de monitoring pour le e-commerce.

Fournit:
- Logs structurés (format JSON)
- Alertes email (seuils critiques)
- Métriques de performance
- Tableau de bord des alertes
"""

import json
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from ecommerce.models import EcommerceLog

logger = logging.getLogger('ecommerce.monitoring')

# ── Seuils d'alerte ──────────────────────────────────────────────────
ALERT_THRESHOLDS = {
    'sync_errors_5min': 5,        # 5+ erreurs en 5 minutes
    'import_errors_5min': 3,      # 3+ erreurs d'import en 5 minutes
    'sync_duration_5min': 120,    # Sync > 120 secondes
    'consecutive_failures': 3,    # 3 échecs consécutifs
    'queue_backlog': 20,          # 20+ éléments en attente
}

# ── État des alertes (évite les doublons) ────────────────────────────
_alert_state: Dict[str, datetime] = {}
_alert_cooldown = timedelta(minutes=15)  # Pas d'alerte doublon < 15min


@dataclass
class StructuredLog:
    """Log structuré au format JSON."""
    timestamp: str
    level: str
    module: str
    event: str
    message: str
    duration_ms: Optional[int] = None
    article_code: Optional[str] = None
    commande_id: Optional[str] = None
    success: Optional[bool] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Sérialise en JSON."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    def to_dict(self) -> Dict:
        """Convertit en dict."""
        return asdict(self)


class MonitoringService:
    """
    Service de monitoring pour le module e-commerce.

    Points d'entrée:
    - log_event(): Journalise un événement structuré
    - check_health(): Vérifie l'état de santé général
    - send_alert(): Envoie une alerte email si seuil dépassé
    - get_metrics(): Retourne les métriques actuelles
    """

    @classmethod
    def log_event(
        cls,
        event: str,
        message: str,
        level: str = 'INFO',
        duration_ms: Optional[int] = None,
        article_code: Optional[str] = None,
        commande_id: Optional[str] = None,
        success: Optional[bool] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Journalise un événement structuré.

        Args:
            event: Nom de l'événement (ex: 'sync_article', 'import_commande')
            message: Description de l'événement
            level: Niveau de log ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
            duration_ms: Durée de l'opération en ms
            article_code: Code article concerné
            commande_id: ID commande concerné
            success: Succès ou échec
            error: Message d'erreur détaillé
            metadata: Données supplémentaires
        """
        log_entry = StructuredLog(
            timestamp=timezone.now().isoformat(),
            level=level,
            module='ecommerce',
            event=event,
            message=message,
            duration_ms=duration_ms,
            article_code=article_code,
            commande_id=commande_id,
            success=success,
            error=error,
            metadata=metadata or {},
        )

        # Log structuré JSON
        json_line = log_entry.to_json()

        # Niveau de log approprié
        log_levels = {
            'DEBUG': logger.debug,
            'INFO': logger.info,
            'WARNING': logger.warning,
            'ERROR': logger.error,
            'CRITICAL': logger.critical,
        }
        log_func = log_levels.get(level.upper(), logger.info)
        log_func(json_line)

        # Persister dans EcommerceLog pour les événements importants
        if level in ('ERROR', 'CRITICAL') or event in (
            'sync_article', 'import_commande', 'sync_stock'
        ):
            try:
                EcommerceLog.objects.create(
                    evenement=event[:50],
                    article_code=article_code or '',
                    commande_id=commande_id or '',
                    success=success if success is not None else (level not in ('ERROR', 'CRITICAL')),
                    message=message[:500],
                    duree_ms=duration_ms,
                )
            except Exception as e:
                logger.error(f"Erreur persistance log: {e}")

        # Vérifier les seuils d'alerte
        if level in ('ERROR', 'CRITICAL'):
            cls._check_alert_thresholds(event)

    @classmethod
    def check_health(cls) -> Dict:
        """
        Vérifie l'état de santé général du module e-commerce.

        Returns:
            Dict avec statut et métriques
        """
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {},
        }

        # 1. Vérifier les logs récents
        try:
            recent_errors = EcommerceLog.objects.filter(
                success=False,
                timestamp__gte=timezone.now() - timedelta(hours=1),
            ).count()
            health_status['checks']['recent_errors_1h'] = recent_errors
            if recent_errors > ALERT_THRESHOLDS['sync_errors_5min']:
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['checks']['recent_errors'] = str(e)

        # 2. Vérifier la file d'attente
        try:
            from ecommerce.models import SyncQueue
            pending = SyncQueue.objects.filter(statut='pending').count()
            failed = SyncQueue.objects.filter(statut='failed').count()
            health_status['checks']['queue_pending'] = pending
            health_status['checks']['queue_failed'] = failed
            if pending > ALERT_THRESHOLDS['queue_backlog']:
                health_status['status'] = 'degraded'
            if failed > 0:
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['checks']['queue'] = str(e)

        # 3. Vérifier la dernière synchronisation
        try:
            from ecommerce.sync.services import FirestoreSyncService
            stats = FirestoreSyncService.get_sync_stats()
            last_sync = stats.get('derniere_synchro')
            if last_sync:
                elapsed = timezone.now() - last_sync
                if elapsed > timedelta(minutes=10):
                    health_status['status'] = 'degraded'
                    health_status['checks']['last_sync_minutes_ago'] = elapsed.total_seconds() / 60
            else:
                health_status['checks']['last_sync'] = 'never'
        except Exception as e:
            health_status['checks']['sync_stats'] = str(e)

        return health_status

    @classmethod
    def send_alert(
        cls,
        subject: str,
        message: str,
        level: str = 'WARNING',
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Envoie une alerte email.

        Args:
            subject: Sujet de l'alerte
            message: Corps du message
            level: Niveau d'alerte
            metadata: Données supplémentaires

        Returns:
            True si l'email a été envoyé
        """
        # Vérifier le cooldown pour éviter les doublons
        alert_key = f"{level}:{subject[:50]}"
        last_sent = _alert_state.get(alert_key)
        if last_sent and (timezone.now() - last_sent) < _alert_cooldown:
            logger.debug(f"Alerte ignorée (cooldown): {alert_key}")
            return False

        # Récupérer les destinataires
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
        if not admin_emails:
            admin_emails = [email for _, email in settings.ADMINS] if hasattr(settings, 'ADMINS') else []
        if not admin_emails:
            logger.warning("Aucun email admin configuré pour les alertes")
            return False

        try:
            # Construire le message HTML
            html_message = render_to_string('ecommerce/email_alert.html', {
                'subject': subject,
                'message': message,
                'level': level,
                'timestamp': timezone.now(),
                'metadata': metadata or {},
                'environment': 'production' if not settings.DEBUG else 'development',
            })

            # Envoyer l'email
            send_mail(
                subject=f"[{level}] E-commerce - {subject}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                html_message=html_message,
                fail_silently=False,
            )

            # Mettre à jour le cooldown
            _alert_state[alert_key] = timezone.now()

            cls.log_event(
                event='alert_sent',
                message=f"Alerte {level}: {subject}",
                level='INFO',
                metadata={'alert_key': alert_key, 'recipients': admin_emails},
            )

            logger.info(f"Alerte envoyée: {subject} -> {admin_emails}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi alerte email: {e}")
            return False

    @classmethod
    def get_metrics(cls, hours: int = 24) -> Dict:
        """
        Retourne les métriques de performance.

        Args:
            hours: Période en heures (défaut: 24h)

        Returns:
            Dict avec métriques
        """
        since = timezone.now() - timedelta(hours=hours)
        metrics = {
            'period_hours': hours,
            'total_events': 0,
            'errors': 0,
            'warnings': 0,
            'success_rate': 100.0,
            'avg_duration_ms': 0,
            'events_by_type': {},
            'errors_by_type': {},
        }

        try:
            logs = EcommerceLog.objects.filter(timestamp__gte=since)
            metrics['total_events'] = logs.count()

            if metrics['total_events'] == 0:
                return metrics

            # Compter les erreurs
            errors = logs.filter(success=False)
            metrics['errors'] = errors.count()

            # Taux de succès
            metrics['success_rate'] = round(
                (metrics['total_events'] - metrics['errors']) / metrics['total_events'] * 100,
                2
            )

            # Durée moyenne
            durations = [l.duree_ms for l in logs if l.duree_ms]
            if durations:
                metrics['avg_duration_ms'] = round(sum(durations) / len(durations), 2)

            # Événements par type
            for log in logs:
                evt = log.evenement or 'unknown'
                metrics['events_by_type'][evt] = metrics['events_by_type'].get(evt, 0) + 1
                if not log.success:
                    metrics['errors_by_type'][evt] = metrics['errors_by_type'].get(evt, 0) + 1

        except Exception as e:
            logger.error(f"Erreur calcul métriques: {e}")

        return metrics

    @classmethod
    def _check_alert_thresholds(cls, event: str) -> None:
        """
        Vérifie si les seuils d'alerte sont dépassés.

        Args:
            event: Type d'événement
        """
        try:
            since = timezone.now() - timedelta(minutes=5)

            # Compter les erreurs récentes
            recent_errors = EcommerceLog.objects.filter(
                success=False,
                timestamp__gte=since,
            ).count()

            if recent_errors >= ALERT_THRESHOLDS['sync_errors_5min']:
                cls.send_alert(
                    subject="Seuil d'erreurs dépassé",
                    message=(
                        f"{recent_errors} erreurs détectées dans les 5 dernières minutes.\n"
                        f"Seuil: {ALERT_THRESHOLDS['sync_errors_5min']}\n"
                        f"Événement: {event}"
                    ),
                    level='ERROR',
                    metadata={'recent_errors': recent_errors, 'threshold': ALERT_THRESHOLDS['sync_errors_5min']},
                )

            # Vérifier les échecs consécutifs
            consecutive = cls._count_consecutive_failures(event)
            if consecutive >= ALERT_THRESHOLDS['consecutive_failures']:
                cls.send_alert(
                    subject="Échecs consécutifs",
                    message=(
                        f"{consecutive} échecs consécutifs pour {event}.\n"
                        f"Seuil: {ALERT_THRESHOLDS['consecutive_failures']}"
                    ),
                    level='ERROR',
                    metadata={'consecutive_failures': consecutive, 'event': event},
                )

        except Exception as e:
            logger.error(f"Erreur vérification seuils: {e}")

    @staticmethod
    def _count_consecutive_failures(event: str) -> int:
        """
        Compte les échecs consécutifs pour un type d'événement.

        Args:
            event: Type d'événement

        Returns:
            Nombre d'échecs consécutifs
        """
        try:
            recent = EcommerceLog.objects.filter(
                evenement=event,
            ).order_by('-timestamp')[:10]

            count = 0
            for log in recent:
                if not log.success:
                    count += 1
                else:
                    break
            return count
        except Exception:
            return 0
