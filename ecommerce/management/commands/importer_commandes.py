"""
Commande Django pour importer les commandes depuis Firestore.

Usage:
    python manage.py importer_commandes
    python manage.py importer_commandes --limit 10
    python manage.py importer_commandes --stats
"""

import logging
from django.core.management.base import BaseCommand
from ecommerce.sync.import_commandes import ImportCommandesService

logger = logging.getLogger('ecommerce.import')


class Command(BaseCommand):
    help = 'Importe les commandes depuis Firestore vers Conbuska'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Nombre maximum de commandes à importer (défaut: toutes)'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Affiche les statistiques d\'import'
        )
    
    def handle(self, *args, **options):
        if options['stats']:
            # Afficher les statistiques
            stats = ImportCommandesService.get_import_stats()
            self.stdout.write(self.style.SUCCESS('\n📊 Statistiques d\'import:'))
            self.stdout.write(f"  Dernier import: {stats['dernier_import'] or 'Jamais'}")
            self.stdout.write(f"  Commandes importées: {stats['commandes_importees']}")
            self.stdout.write(f"  Commandes en erreur: {stats['commandes_en_erreur']}")
            
            if stats['dernieres_erreurs']:
                self.stdout.write(self.style.WARNING('\n⚠️  Dernières erreurs:'))
                for erreur in stats['dernieres_erreurs']:
                    self.stdout.write(f"  - {erreur}")
            return
        
        # Lancer l'import
        self.stdout.write(self.style.SUCCESS('\n🔄 Import des commandes...'))
        
        try:
            resultat = ImportCommandesService.importer_commandes(
                limit=options.get('limit')
            )
            
            # Afficher les résultats
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Import terminé: {resultat['succes']} succès, "
                    f"{resultat['erreurs']} erreurs"
                )
            )
            
            # Détails des erreurs
            if resultat['erreurs'] > 0:
                self.stdout.write(self.style.WARNING('\n❌ Détails des erreurs:'))
                for detail in resultat['details']:
                    if not detail['succes']:
                        self.stdout.write(
                            f"  - {detail['doc_id']}: {detail['erreur']}"
                        )
            
            # Détails des succès
            if resultat['succes'] > 0:
                self.stdout.write(self.style.SUCCESS('\n✓ Commandes importées:'))
                for detail in resultat['details']:
                    if detail['succes']:
                        self.stdout.write(
                            f"  - {detail['doc_id']}: Facture #{detail['facture_numero']} "
                            f"({detail['client_nom']})"
                        )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Erreur fatale: {e}')
            )
            logger.error(f"Erreur fatale import: {e}", exc_info=True)
            raise