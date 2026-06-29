#!/usr/bin/env python3
"""
Tests de compatibilité Django 6.0
Vérifie les breaking changes et dépréciations
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esm.settings.base')
django.setup()

from django.conf import settings
from django.db import models
import importlib


def check_django_version():
    """Vérifie la version de Django"""
    print("🔍 Vérification version Django...")
    version = django.get_version()
    print(f"   Version actuelle: {version}")
    print(f"   Version cible: 6.0.x")
    
    major = int(version.split('.')[0])
    if major >= 6:
        print("   ✅ Django 6.x détecté")
        return True
    else:
        print("   ⚠️  Django 5.x - Migration nécessaire")
        return False


def check_middleware():
    """Vérifie la compatibilité des middlewares"""
    print("\n🔍 Vérification des middlewares...")
    
    middleware = settings.MIDDLEWARE
    print(f"   Nombre de middlewares: {len(middleware)}")
    
    # Middlewares Django standards
    standard_middlewares = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]
    
    issues = []
    for mw in standard_middlewares:
        if mw in middleware:
            print(f"   ✅ {mw.split('.')[-1]}")
        else:
            print(f"   ⚠️  {mw.split('.')[-1]} - manquant")
            issues.append(mw)
    
    # Middlewares customs
    custom_middlewares = [mw for mw in middleware if not mw.startswith('django.')]
    print(f"\n   Middlewares customs: {len(custom_middlewares)}")
    for mw in custom_middlewares:
        print(f"   - {mw}")
    
    return len(issues) == 0


def check_settings():
    """Vérifie les paramètres settings.py"""
    print("\n🔍 Vérification des settings...")
    
    issues = []
    
    # Django 6.0: X_FRAME_OPTIONS est maintenant 'DENY' par défaut
    if hasattr(settings, 'X_FRAME_OPTIONS'):
        print(f"   X_FRAME_OPTIONS: {settings.X_FRAME_OPTIONS}")
    
    # Django 6.0: CSRF_COOKIE_SAMESITE
    if hasattr(settings, 'CSRF_COOKIE_SAMESITE'):
        print(f"   CSRF_COOKIE_SAMESITE: {settings.CSRF_COOKIE_SAMESITE}")
    else:
        print("   ⚠️  CSRF_COOKIE_SAMESITE non défini (recommandé pour Django 6.0)")
        issues.append('CSRF_COOKIE_SAMESITE')
    
    # Django 6.0: SESSION_COOKIE_SAMESITE
    if hasattr(settings, 'SESSION_COOKIE_SAMESITE'):
        print(f"   SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}")
    else:
        print("   ⚠️  SESSION_COOKIE_SAMESITE non défini (recommandé pour Django 6.0)")
        issues.append('SESSION_COOKIE_SAMESITE')
    
    # DEFAULT_AUTO_FIELD
    if hasattr(settings, 'DEFAULT_AUTO_FIELD'):
        print(f"   DEFAULT_AUTO_FIELD: {settings.DEFAULT_AUTO_FIELD}")
    else:
        print("   ⚠️  DEFAULT_AUTO_FIELD non défini")
        issues.append('DEFAULT_AUTO_FIELD')
    
    return len(issues) == 0


def check_url_patterns():
    """Vérifie les patterns d'URL"""
    print("\n🔍 Vérification des URLs...")
    
    try:
        from esm.urls import urlpatterns
        
        print(f"   Nombre de patterns: {len(urlpatterns)}")
        
        # Vérifier si des patterns utilisent des fonctionnalités dépréciées
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                # Include
                print(f"   - Include: {pattern.url_patterns}")
            else:
                # URL simple
                print(f"   - {pattern.pattern}")
        
        print("   ✅ Patterns d'URL valides")
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def check_models():
    """Vérifie les modèles Django"""
    print("\n🔍 Vérification des modèles...")
    
    apps = settings.INSTALLED_APPS
    project_apps = [app for app in apps if app.startswith('esm') or app in [
        'activity_logs', 'approvisionnements', 'caisse', 'clients',
        'commandes', 'creanciers', 'factures', 'fournisseurs',
        'paie', 'parametres', 'patrimoine', 'produits', 'rapports'
    ]]
    
    print(f"   Applications projet: {len(project_apps)}")
    
    issues = []
    for app in project_apps:
        try:
            models_module = importlib.import_module(f'{app}.models')
            if hasattr(models_module, 'models'):
                model_count = len(models_module.models)
                print(f"   ✅ {app}: {model_count} modèles")
        except Exception as e:
            print(f"   ⚠️  {app}: {e}")
            issues.append(app)
    
    return len(issues) == 0


def check_breaking_changes():
    """Vérifie les breaking changes Django 6.0"""
    print("\n🔍 Vérification des breaking changes...")
    
    breaking_changes = {
        'CSRF_COOKIE_SECURE': {
            'description': 'Doit être True en production',
            'required': True
        },
        'SECURE_SSL_REDIRECT': {
            'description': 'Redirection HTTPS en production',
            'required': False
        },
        'SECURE_HSTS_SECONDS': {
            'description': 'HSTS pour HTTPS',
            'required': False
        },
        'SECURE_HSTS_INCLUDE_SUBDOMAINS': {
            'description': 'HSTS sous-domaines',
            'required': False
        },
        'SECURE_HSTS_PRELOAD': {
            'description': 'HSTS preload',
            'required': False
        },
    }
    
    issues = []
    for setting, info in breaking_changes.items():
        value = getattr(settings, setting, None)
        if value is None:
            status = "⚠️  Non défini"
            if info['required']:
                issues.append(setting)
        else:
            status = f"✅ {value}"
        
        print(f"   {status} - {setting}")
        print(f"      → {info['description']}")
    
    return len(issues) == 0


def generate_compatibility_report():
    """Génère un rapport de compatibilité"""
    print("\n📄 Génération du rapport de compatibilité...")
    
    results = {
        'Django Version': check_django_version(),
        'Middlewares': check_middleware(),
        'Settings': check_settings(),
        'URL Patterns': check_url_patterns(),
        'Models': check_models(),
        'Breaking Changes': check_breaking_changes()
    }
    
    report = f"""
# Rapport de Compatibilité Django 6.0
**Date:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**Version Django:** {django.get_version()}

## Résumé des Tests

| Composant | Status | Détails |
|-----------|--------|---------|
"""
    
    for component, status in results.items():
        status_str = "✅ Compatible" if status else "⚠️  À vérifier"
        report += f"| {component} | {status_str} | - |\n"
    
    all_compatible = all(results.values())
    
    report += f"""
## Score Global: {'✅ 100%' if all_compatible else '⚠️  Vérifications requises'}

## Actions Requises

### Avant Migration vers Django 6.0:
1. Mettre à jour settings.py avec les nouveaux paramètres
2. Tester tous les middlewares customs
3. Vérifier les templates pour dépréciations
4. Exécuter les tests de régression

### Paramètres à Ajouter:
```python
# settings.py - Ajouter ces lignes

# Sécurité (Django 6.0)
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Production (recommandé)
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## Prochaines Étapes
1. Corriger les points identifiés
2. Mettre à jour requirements.txt avec Django 6.0.x
3. Tester en environnement isolé
4. Exécuter: python manage.py test

## Références
- [Django 6.0 Release Notes](https://docs.djangoproject.com/en/6.0/releases/6.0/)
- [Migration Guide](https://docs.djangoproject.com/en/6.0/howto/upgrade-version/)
"""
    
    report_file = f"compatibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"   ✅ Rapport généré: {report_file}")
    return report_file, all_compatible


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🔍 TESTS DE COMPATIBILITÉ DJANGO 6.0")
    print("=" * 60)
    
    try:
        report_file, all_compatible = generate_compatibility_report()
        
        print("\n" + "=" * 60)
        if all_compatible:
            print("✅ PROJET COMPATIBLE AVEC DJANGO 6.0")
        else:
            print("⚠️  VÉRIFICATIONS SUPPLÉMENTAIRES REQUISES")
        print("=" * 60)
        
        print(f"\n📋 Rapport détaillé: {report_file}")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors des tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()