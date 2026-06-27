"""
Commande Django pour synchroniser manuellement les articles vers Firestore.

Usage :
    python manage.py sync_firestore            # Sync incrémentale
    python manage.py sync_firestore --all       # Sync force tous les articles
    python manage.py sync_firestore --article 42  # Sync un article spécifique
    python manage.py sync_firestore --stats     # Afficher les statistiques
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger('ecommerce.sync')


class Command(BaseCommand):
    help = 'Synchronise les articles Conbuska vers Firestore'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            dest='force_all',
            help='Forcer la synchronisation de tous les articles publiés'
        )
        parser.add_argument(
            '--article',
            type=str,
            dest='article_code',
            help='Code de l\'article à synchroniser (ex: 1000)'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            dest='show_stats',
            help='Afficher les statistiques de synchronisation'
        )

    def handle(self, *args, **options):
        from ecommerce.sync.services import FirestoreSyncService
        from produits.models import Article

        # Afficher les statistiques
        if options.get('show_stats'):
            stats = FirestoreSyncService.get_sync_stats()
            self._display_stats(stats)
            return

        # Synchroniser un article spécifique
        article_code = options.get('article_code')
        if article_code:
            self._sync_single_article(article_code)
            return

        # Synchronisation par lots
        force_all = options.get('force_all', False)
        self._sync_all(force_all)

    def _sync_single_article(self, article_code: str):
        """Synchronise un article spécifique."""
        from ecommerce.sync.services import FirestoreSyncService
        from produits.models import Article

        try:
            article = Article.objects.get(code=article_code)
        except Article.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Article {article_code} introuvable")
            )
            return

        self.stdout.write(
            f"Synchronisation de l'article {article.code} - {article.designation}..."
        )

        success = FirestoreSyncService.sync_article(article, force=True)

        if success:
            self.stdout.write(self.style.SUCCESS(f"✓ Article {article_code} synchronisé"))
        else:
            self.stderr.write(
                self.style.ERROR(f"✗ Erreur lors de la sync de {article_code}")
            )

    def _sync_all(self, force_all: bool):
        """Synchronise tous les articles."""
        from ecommerce.sync.services import FirestoreSyncService

        mode = "complète" if force_all else "incrémentale"
        self.stdout.write(
            f"Début de la synchronisation {mode} des articles..."
        )

        start_time = timezone.now()
        success, errors = FirestoreSyncService.sync_all(force=force_all)
        duration = (timezone.now() - start_time).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Synchronisation terminée en {duration:.1f}s "
                f"({success} succès, {errors} échecs)"
            )
        )

        # Afficher les stats
        stats = FirestoreSyncService.get_sync_stats()
        self._display_stats(stats)

    def _display_stats(self, stats: dict):
        """Affiche les statistiques de synchronisation."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n📊 Statistiques de synchronisation"))
        self.stdout.write("-" * 40)
        
        derniere_sync = stats.get('derniere_synchro')
        if derniere_sync:
            if hasattr(derniere_sync, 'strftime'):
                self.stdout.write(f"Dernière synchronisation : {derniere_sync}")
            else:
                self.stdout.write(f"Dernière synchronisation : {derniere_sync}")
        else:
            self.stdout.write("Dernière synchronisation : Jamais")
        
        self.stdout.write(f"Articles synchronisés   : {stats.get('articles_synchronises', 0)}")
        self.stdout.write(f"Articles supprimés      : {stats.get('articles_supprimes', 0)}")
        
        erreurs = stats.get('dernieres_erreurs', [])
        if erreurs:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  Dernières erreurs ({len(erreurs)}) :")
            )
            for err in erreurs[-5:]:
                self.stdout.write(f"  • {err}")
        else:
            self.stdout.write("\n✅ Aucune erreur")