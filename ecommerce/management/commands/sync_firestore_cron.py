"""
Commande cron pour synchronisation périodique Firestore.
À exécuter toutes les 5 minutes via le planificateur système.

Usage:
    # Toutes les 5 minutes
    python manage.py sync_firestore_cron

    # Mode verbose (logs détaillés)
    python manage.py sync_firestore_cron --verbose

    # Test sans écriture réelle
    python manage.py sync_firestore_cron --dry-run
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ecommerce.models import EcommerceLog, SyncQueue

logger = logging.getLogger('ecommerce.cron')


class Command(BaseCommand):
    help = 'Cron job: synchronisation périodique Firestore (toutes les 5 min)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Afficher les logs détaillés',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Simulation sans écriture réelle',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        dry_run = options.get('dry_run', False)

        start_time = time.time()

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n🔄 [CRON] Synchronisation Firestore - {timezone.now().isoformat()}"
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODE DRY-RUN - Aucune écriture réelle\n"))

        # ── Étape 1 : Purge des SyncQueue en échec (retry) ──────────
        self._step("1/4", "Retry des sync échouées", dry_run)

        if dry_run:
            failed_count = SyncQueue.objects.filter(statut='failed').count()
            self.stdout.write(f"  → {failed_count} sync échouées à retenter")
        else:
            retry_result = self._retry_failed_syncs(verbose)
            self.stdout.write(f"  → {retry_result['traitees']} traitées, "
                              f"{retry_result['succes']} succès, {retry_result['echecs']} échecs")

        # ── Étape 2 : Synchronisation incrémentale ──────────────────
        self._step("2/4", "Synchronisation incrémentale articles publiés")

        try:
            from ecommerce.sync.services import FirestoreSyncService

            if dry_run:
                from produits.models import Article
                nb_articles = Article.objects.filter(est_publie=True).count()
                self.stdout.write(f"  → {nb_articles} articles publiés à synchroniser (simulé)")
            else:
                success, errors = FirestoreSyncService.sync_all(force=False)
                self.stdout.write(
                    f"  → {success} synchronisés, {errors} échecs"
                )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"  ✗ Erreur sync: {e}")
            )
            if verbose:
                import traceback
                self.stderr.write(traceback.format_exc())

        # ── Étape 3 : Nettoyage des logs anciens (> 30 jours) ──────
        self._step("3/4", "Nettoyage des logs anciens (> 30 jours)")

        if dry_run:
            seuil = timezone.now() - timedelta(days=30)
            old_logs = EcommerceLog.objects.filter(timestamp__lt=seuil).count()
            self.stdout.write(f"  → {old_logs} logs à purger (simulé)")
        else:
            purged = self._purge_old_logs()
            self.stdout.write(f"  → {purged} logs purgés")

        # ── Étape 4 : Statistiques ──────────────────────────────────
        self._step("4/4", "Collecte des statistiques")

        try:
            from ecommerce.sync.services import FirestoreSyncService
            stats = FirestoreSyncService.get_sync_stats()
        except Exception:
            stats = {}

        elapsed = time.time() - start_time

        # Journalisation structurée
        self._log_sync_result({
            'duree_secondes': round(elapsed, 2),
            'dry_run': dry_run,
            'stats': stats,
        })

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ [CRON] Terminé en {elapsed:.1f}s\n"
        ))

    # ── Méthodes internes ────────────────────────────────────────────

    def _step(self, num: str, label: str, dry_run: bool = False):
        """Affiche une étape du cron."""
        self.stdout.write(self.style.MIGRATE_LABEL(
            f"\n{num} {label}"
        ))

    def _retry_failed_syncs(self, verbose: bool = False) -> Dict:
        """
        Retente les synchronisations échouées.

        Returns:
            Dict avec {'traitees': int, 'succes': int, 'echecs': int}
        """
        from ecommerce.sync.services import FirestoreSyncService
        from produits.models import Article

        failed_syncs = SyncQueue.objects.filter(statut='failed')[:50]
        traitees = 0
        succes = 0
        echecs = 0

        for sync in failed_syncs:
            traitees += 1
            try:
                article = sync.article
                ok = FirestoreSyncService.sync_article(article, force=True)
                if ok:
                    sync.statut = 'completed'
                    sync.date_traitement = timezone.now()
                    sync.save(update_fields=['statut', 'date_traitement'])
                    succes += 1
                    if verbose:
                        self.stdout.write(f"    ✓ {article.code} - {article.designation}")
                else:
                    sync.tentatives += 1
                    sync.save(update_fields=['tentatives'])
                    echecs += 1
            except Article.DoesNotExist:
                sync.delete()
                echecs += 1
            except Exception as e:
                sync.tentatives += 1
                sync.erreur = str(e)[:500]
                sync.save(update_fields=['tentatives', 'erreur'])
                echecs += 1
                if verbose:
                    self.stderr.write(f"    ✗ {sync.article_id}: {e}")

        return {
            'traitees': traitees,
            'succes': succes,
            'echecs': echecs,
        }

    def _purge_old_logs(self) -> int:
        """
        Supprime les logs de synchronisation de plus de 30 jours.

        Returns:
            Nombre de logs supprimés
        """
        seuil = timezone.now() - timedelta(days=30)
        deleted, _ = EcommerceLog.objects.filter(
            timestamp__lt=seuil
        ).delete()
        return deleted

    def _log_sync_result(self, data: Dict):
        """
        Journalise le résultat de la synchronisation.

        Args:
            data: Dict avec les métriques
        """
        logger.info(
            "[CRON] Synchronisation terminée | "
            f"durée={data['duree_secondes']}s | "
            f"dry_run={data['dry_run']} | "
            f"stats={data.get('stats', {})}"
        )

        # Journalisation dans le modèle EcommerceLog
        if not data.get('dry_run'):
            try:
                EcommerceLog.objects.create(
                    evenement='sync_article',
                    success=True,
                    message=f"Cron sync terminé en {data['duree_secondes']}s",
                    duree_ms=int(data['duree_secondes'] * 1000),
                )
            except Exception:
                pass
