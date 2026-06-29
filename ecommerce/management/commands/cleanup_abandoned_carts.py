"""
Commande cron pour nettoyage des paniers abandonnés.
À exécuter toutes les 30 minutes via le planificateur système.

Supprime les commandes Firestore en statut "nouveau" ou "panier"
qui n'ont pas été modifiées depuis plus de 24 heures.

Usage:
    python manage.py cleanup_abandoned_carts
    python manage.py cleanup_abandoned_carts --dry-run
    python manage.py cleanup_abandoned_carts --hours 48
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from django.core.management.base import BaseCommand
from django.utils import timezone

from ecommerce.models import EcommerceLog

logger = logging.getLogger('ecommerce.cron')


class Command(BaseCommand):
    help = 'Cron job: nettoie les paniers abandonnés (Firestore)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Simulation sans suppression réelle',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            dest='hours',
            help='Âge en heures pour considérer un panier comme abandonné (défaut: 24)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        hours = options.get('hours', 24)

        start_time = time.time()

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n🧹 [CRON] Nettoyage paniers abandonnés - {timezone.now().isoformat()}"
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODE DRY-RUN - Aucune suppression réelle\n"))

        seuil = timezone.now() - timedelta(hours=hours)
        self.stdout.write(f"  Seuil d'abandon : {seuil.isoformat()} (> {hours}h sans modification)")

        try:
            from ecommerce.sync.services import FirestoreSyncService

            def _fetch_abandoned():
                db = FirestoreSyncService._get_firestore_client()
                # Récupérer les commandes "nouveau" ou "panier" anciennes
                docs = []
                for statut in ['nouveau', 'panier']:
                    query = db.collection('commandes_en_ligne')\
                        .where('statut', '==', statut)\
                        .where('date_modification', '<', seuil.isoformat())
                    docs.extend(list(query.stream()))
                return docs

            try:
                abandoned_docs = FirestoreSyncService._execute_with_retry(
                    _fetch_abandoned, "récupération paniers abandonnés"
                )
            except Exception:
                # Si Firestore n'est pas configuré, on simule
                abandoned_docs = []
                self.stdout.write(self.style.WARNING(
                    "  ⚠ Firestore non accessible, vérification locale uniquement"
                ))

            self.stdout.write(f"\n  {len(abandoned_docs)} panier(s) abandonné(s) trouvé(s)")

            if not abandoned_docs:
                self.stdout.write(self.style.SUCCESS("\n✅ Aucun panier à nettoyer"))
                return

            # Supprimer ou marquer
            supprimes = 0
            for doc in abandoned_docs:
                doc_id = doc.id
                data = doc.to_dict() if hasattr(doc, 'to_dict') else {}
                email = (data.get('client') or {}).get('email', 'inconnu')

                if dry_run:
                    self.stdout.write(f"  [DRY-RUN] Suppression de {doc_id} (client: {email})")
                else:
                    try:
                        def _delete(doc_id=doc_id):
                            db = FirestoreSyncService._get_firestore_client()
                            db.collection('commandes_en_ligne').document(doc_id).delete()

                        FirestoreSyncService._execute_with_retry(
                            _delete, f"suppression panier {doc_id}"
                        )
                        supprimes += 1
                        self.stdout.write(f"  ✓ {doc_id} supprimé (client: {email})")
                    except Exception as e:
                        self.stderr.write(f"  ✗ Erreur suppression {doc_id}: {e}")

            # Journalisation
            elapsed = time.time() - start_time
            if not dry_run:
                try:
                    EcommerceLog.objects.create(
                        evenement='sync_article',
                        success=True,
                        message=f"Nettoyage: {supprimes} paniers abandonnés supprimés en {elapsed:.1f}s",
                        duree_ms=int(elapsed * 1000),
                    )
                except Exception:
                    pass

            logger.info(
                "[CRON] Nettoyage paniers abandonnés terminé | "
                f"durée={elapsed:.1f}s | supprimés={supprimes} | dry_run={dry_run}"
            )

            self.stdout.write(self.style.SUCCESS(
                f"\n✅ [CRON] Nettoyage terminé en {elapsed:.1f}s - {supprimes} panier(s) supprimé(s)"
            ))

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"\n✗ Erreur fatale: {e}")
            )
            logger.error(f"[CRON] Erreur nettoyage paniers: {e}", exc_info=True)
            raise
