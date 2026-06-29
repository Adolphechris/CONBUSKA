#!/usr/bin/env python3
"""
Script de rollback v2.0 → v1.0
Permet de revenir à la version précédente en cas de problème
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esm.settings.base')
django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


def restore_database(backup_file):
    """Restaure la base de données depuis un backup"""
    print(f"💾 Restauration de la base de données depuis: {backup_file}")
    
    if not os.path.exists(backup_file):
        print(f"   ❌ Fichier de backup introuvable: {backup_file}")
        return False
    
    db_name = os.environ.get('DB_NAME', 'esm')
    db_user = os.environ.get('DB_USER', 'postgres')
    
    cmd = f"pg_restore -U {db_user} -d {db_name} --clean --if-exists {backup_file}"
    
    print(f"   Commande: {cmd}")
    print(f"   ⚠️  Cette opération va ÉCRASER la base de données actuelle")
    
    confirm = input("   Confirmer la restauration ? (oui/non): ")
    if confirm.lower() != 'oui':
        print("   ❌ Restauration annulée")
        return False
    
    os.system(cmd)
    print(f"   ✅ Base de données restaurée")
    return True


def restore_media(backup_file):
    """Restaure les fichiers media"""
    print(f"\n📸 Restauration des media depuis: {backup_file}")
    
    if not os.path.exists(backup_file):
        print(f"   ❌ Fichier de backup introuvable: {backup_file}")
        return False
    
    os.system(f"tar -xzf {backup_file}")
    print(f"   ✅ Media restaurés")
    return True


def restore_config(backup_file):
    """Restaure la configuration"""
    print(f"\n⚙️  Restauration de la configuration depuis: {backup_file}")
    
    if not os.path.exists(backup_file):
        print(f"   ❌ Fichier de backup introuvable: {backup_file}")
        return False
    
    os.system(f"tar -xzf {backup_file}")
    print(f"   ✅ Configuration restaurée")
    return True


def checkout_git_tag(tag_name):
    """Checkout un tag Git"""
    print(f"\n🏷️  Checkout du tag Git: {tag_name}")
    
    os.system(f"git checkout {tag_name}")
    print(f"   ✅ Code restauré au tag {tag_name}")
    return True


def validate_rollback():
    """Valide que le rollback a réussi"""
    print("\n🔍 Validation du rollback...")
    
    try:
        # Vérifier que Django fonctionne
        from django.conf import settings
        print(f"   ✅ Django configuré: {settings.DATABASES['default']['ENGINE']}")
        
        # Vérifier les modèles
        from factures.models import Facture
        count = Facture.objects.count()
        print(f"   ✅ Factures en base: {count}")
        
        # Vérifier la version
        import django
        print(f"   ✅ Version Django: {django.get_version()}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur de validation: {e}")
        return False


def main():
    """Fonction principale de rollback"""
    print("=" * 60)
    print("⚠️  ROLLBACK v2.0 → v1.0")
    print("=" * 60)
    print()
    
    # Lister les backups disponibles
    backup_dir = "backups"
    if os.path.exists(backup_dir):
        backups = sorted([f for f in os.listdir(backup_dir) if 'v1_backup' in f], reverse=True)
        
        if backups:
            print("📦 Backups disponibles:")
            for i, backup in enumerate(backups[:5], 1):
                print(f"   {i}. {backup}")
            print()
            
            choice = input("Numéro du backup à restaurer (ou 'quit' pour annuler): ")
            
            if choice.lower() == 'quit':
                print("❌ Rollback annulé")
                return
            
            try:
                backup_name = backups[int(choice) - 1]
                backup_prefix = backup_name.replace('_database.dump', '').replace('_media.tar.gz', '').replace('_config.tar.gz', '').replace('_manifest.txt', '')
            except (ValueError, IndexError):
                print("❌ Choix invalide")
                return
        else:
            print("⚠️  Aucun backup v1 trouvé dans backups/")
            backup_prefix = input("Entrez le préfixe du backup manuellement: ")
    else:
        print("❌ Dossier backups/ introuvable")
        return
    
    print(f"\n📦 Backup sélectionné: {backup_prefix}")
    print()
    
    try:
        with transaction.atomic():
            # Demander confirmation
            print("⚠️  ATTENTION: Cette opération va:")
            print(f"   1. Restaurer la base de données")
            print(f"   2. Restaurer les fichiers media")
            print(f"   3. Restaurer la configuration")
            print(f"   4. Checkout le tag Git correspondant")
            print()
            
            confirm = input("Êtes-vous sûr ? (oui/non): ")
            if confirm.lower() != 'oui':
                print("❌ Rollback annulé")
                return
            
            # 1. Restaurer la base de données
            db_backup = f"{backup_dir}/{backup_prefix}_database.dump"
            restore_database(db_backup)
            
            # 2. Restaurer les media
            media_backup = f"{backup_dir}/{backup_prefix}_media.tar.gz"
            if os.path.exists(media_backup):
                restore_media(media_backup)
            
            # 3. Restaurer la config
            config_backup = f"{backup_dir}/{backup_prefix}_config.tar.gz"
            if os.path.exists(config_backup):
                restore_config(config_backup)
            
            # 4. Checkout Git tag
            # Extraire le tag depuis le manifeste
            manifest_file = f"{backup_dir}/{backup_prefix}_manifest.txt"
            if os.path.exists(manifest_file):
                with open(manifest_file, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'Tag Git' in line:
                            tag = line.split(': ')[1].strip()
                            checkout_git_tag(tag)
                            break
            
            # 5. Valider
            if validate_rollback():
                print("\n" + "=" * 60)
                print("✅ ROLLBACK EFFECTUÉ AVEC SUCCÈS")
                print("=" * 60)
                print("\n📋 Actions à faire:")
                print("   1. Vérifier les données")
                print("   2. Exécuter: python manage.py test")
                print("   3. Valider le fonctionnement")
            else:
                print("\n❌ ERREUR: Rollback incomplet")
                
    except Exception as e:
        print(f"\n❌ ERREUR lors du rollback: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()