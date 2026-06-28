"""
Test de connexion Firebase pour la synchronisation.
Vérifie que:
- Firebase est correctement initialisé
- Firestore est accessible
- Storage est accessible
"""

import os
import sys
import django
from pathlib import Path

# Ajouter le projet au path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esm.settings.development')
django.setup()

import logging
from django.conf import settings

# Configuration du logging pour voir les messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ecommerce.sync')


def test_firebase_config():
    """Vérifie que la configuration Firebase est présente."""
    print("\n" + "="*60)
    print("TEST 1: Configuration Firebase")
    print("="*60)
    
    errors = []
    
    # Vérifier les variables d'environnement
    credentials = getattr(settings, 'FIREBASE_CREDENTIALS', '')
    storage_bucket = getattr(settings, 'FIREBASE_STORAGE_BUCKET', '')
    project_id = getattr(settings, 'FIREBASE_PROJECT_ID', '')
    
    if not credentials:
        errors.append("FIREBASE_CREDENTIALS manquant dans settings")
    else:
        print(f"✅ FIREBASE_CREDENTIALS: {credentials}")
    
    if not storage_bucket:
        errors.append("FIREBASE_STORAGE_BUCKET manquant dans settings")
    else:
        print(f"✅ FIREBASE_STORAGE_BUCKET: {storage_bucket}")
    
    if not project_id:
        errors.append("FIREBASE_PROJECT_ID manquant dans settings")
    else:
        print(f"✅ FIREBASE_PROJECT_ID: {project_id}")
    
    if errors:
        print("\n❌ ERREURS:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ Configuration Firebase OK")
    return True


def test_firestore_connection():
    """Teste la connexion à Firestore."""
    print("\n" + "="*60)
    print("TEST 2: Connexion Firestore")
    print("="*60)
    
    try:
        from ecommerce.sync.services import FirestoreSyncService
        
        # Récupérer le client Firestore
        db = FirestoreSyncService._get_firestore_client()
        
        # Tester une lecture simple
        collections = db.collections()
        print(f"✅ Connexion Firestore établie")
        print(f"✅ Collections accessibles: {list(collections)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion Firestore: {e}")
        return False


def test_storage_connection():
    """Teste la connexion à Firebase Storage."""
    print("\n" + "="*60)
    print("TEST 3: Connexion Firebase Storage")
    print("="*60)
    
    try:
        from ecommerce.sync.storage import FirebaseStorageService
        
        # Tester la connexion en listant les fichiers (max 1)
        bucket = FirebaseStorageService._get_bucket()
        blobs = list(bucket.list_blobs(max_results=1))
        
        print(f"✅ Connexion Storage établie")
        print(f"✅ Bucket: {bucket.name}")
        print(f"✅ Fichiers dans le bucket: {len(blobs)} (max 1 affiché)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion Storage: {e}")
        return False


def test_article_sync():
    """Teste la synchronisation d'un article."""
    print("\n" + "="*60)
    print("TEST 4: Synchronisation article test")
    print("="*60)
    
    try:
        from produits.models import Article
        from ecommerce.sync.services import FirestoreSyncService
        
        # Récupérer un article publié (s'il existe)
        article = Article.objects.filter(est_publie=True).first()
        
        if not article:
            print("⚠️  Aucun article publié trouvé, test ignoré")
            return True
        
        print(f"Article test: {article.designation} (code: {article.code})")
        
        # Tester la synchronisation
        success = FirestoreSyncService.sync_article(article, force=True)
        
        if success:
            print(f"✅ Article synchronisé avec succès")
            
            # Vérifier les stats
            stats = FirestoreSyncService.get_sync_stats()
            print(f"✅ Dernière sync: {stats['derniere_synchro']}")
            print(f"✅ Articles synchronisés: {stats['articles_synchronises']}")
            
            return True
        else:
            print(f"❌ Échec de la synchronisation")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test de sync: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécute tous les tests."""
    print("\n" + "="*60)
    print("TESTS DE CONNEXION FIREBASE")
    print("="*60)
    
    results = []
    
    # Test 1: Configuration
    results.append(("Configuration", test_firebase_config()))
    
    # Test 2: Firestore
    results.append(("Firestore", test_firestore_connection()))
    
    # Test 3: Storage
    results.append(("Storage", test_storage_connection()))
    
    # Test 4: Sync article
    results.append(("Sync article", test_article_sync()))
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) échoué(s)")
        return 1


if __name__ == '__main__':
    sys.exit(main())