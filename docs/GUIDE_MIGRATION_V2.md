# 📚 GUIDE DE MIGRATION v1.0 → v2.0

**Version:** 2.0.0  
**Date:** 29 Juin 2026  
**Branche:** `release/v2.0`

---

## 📋 TABLE DES MATIÈRES

1. [Vue d'ensemble](#vue-densemble)
2. [Prérequis](#prérequis)
3. [Étapes de migration](#étapes-de-migration)
4. [Validation](#validation)
5. [Rollback](#rollback)
6. [FAQ](#faq)

---

## 🎯 VUE D'ENSEMBLE

Cette migration concerne :
- **Montée de version Django:** 5.2.1 → 6.0.x
- **Nouvelles fonctionnalités:** API REST, permissions avancées
- **Améliorations:** Architecture, sécurité, maintenabilité

### ⚠️  IMPORTANT

**Cette migration est irréversible sans backup.** Assurez-vous d'avoir :
- ✅ Backup de la base de données
- ✅ Backup des fichiers media
- ✅ Tag Git de la version v1.0
- ✅ Tests de rollback effectués

---

## 📦 PRÉREQUIS

### Vérifications Préalables

```bash
# 1. Vérifier la version de Python
python3 --version  # Doit être 3.12+

# 2. Vérifier PostgreSQL
psql --version  # Doit être 14+

# 3. Vérifier l'espace disque
df -h  # Au moins 5GB libres

# 4. Vérifier les permissions
ls -la scripts/  # Doit avoir les droits d'exécution
```

### Environnement de Test

**OBLIGATOIRE:** Tester d'abord sur un environnement isolé

```bash
# Créer un environnement de test
python3 -m venv venv_test
source venv_test/bin/activate
pip install -r requirements.txt
```

---

## 🚀 ÉTAPES DE MIGRATION

### Étape 1: Sauvegarde (OBLIGATOIRE)

```bash
# Rendre le script exécutable
chmod +x scripts/backup_v1.sh

# Exécuter la sauvegarde
./scripts/backup_v1.sh
```

**Vérifier:** Les fichiers suivants doivent être créés dans `backups/`:
- `esm_v1_backup_YYYYMMDD_HHMMSS_database.dump`
- `esm_v1_backup_YYYYMMDD_HHMMSS_media.tar.gz`
- `esm_v1_backup_YYYYMMDD_HHMMSS_config.tar.gz`
- `esm_v1_backup_YYYYMMDD_HHMMSS_manifest.txt`

### Étape 2: Vérification de Compatibilité

```bash
# Tester la compatibilité Django 6.0
python3 scripts/test_django60_compatibility.py
```

**Analyser le rapport:** `compatibility_report_YYYYMMDD_HHMMSS.md`

**Actions requises:**
- [ ] Corriger les settings manquants
- [ ] Vérifier les middlewares customs
- [ ] Tester les templates

### Étape 3: Migration du Code

```bash
# 1. Se placer sur la branche release/v2.0
git checkout release/v2.0

# 2. Mettre à jour les dépendances
pip install --upgrade Django==6.0.x
pip install djangorestframework==3.15.2

# 3. Mettre à jour requirements.txt
# (Déjà fait dans la branche)

# 4. Appliquer les migrations Django
python3 manage.py makemigrations
python3 manage.py migrate
```

### Étape 4: Tests de Régression

```bash
# Exécuter tous les tests
python3 manage.py test

# Tests spécifiques factures
python3 manage.py test factures.tests.test_validation_stock_lots -v 2

# Tests spécifiques caisse
python3 manage.py test caisse.tests -v 2
```

**Résultat attendu:** Tous les tests doivent passer ✅

### Étape 5: Validation Fonctionnelle

```bash
# 1. Démarrer le serveur
python3 manage.py runserver

# 2. Tester manuellement dans le navigateur
# - Dashboard
# - Factures
# - Caisse
# - Approvisionnements
# - Rapports
```

**Checklist de validation:**
- [ ] Dashboard s'affiche correctement
- [ ] Création de facture fonctionne
- [ ] Validation stock par lots OK
- [ ] Double devise USD/FC fonctionne
- [ ] Snapshots patrimoine générés
- [ ] Exports PDF fonctionnels
- [ ] Boutique e-commerce accessible

### Étape 6: Migration des Données (si nécessaire)

```bash
# Exécuter le script de migration
python3 scripts/migrate_v1_to_v2.py
```

**Vérifier:**
- [ ] Données double devise cohérentes
- [ ] Snapshots patrimoine présents
- [ ] Taux de change historiques conservés

---

## ✅ VALIDATION

### Tests Automatiques

```bash
# Suite complète de tests
python3 manage.py test --verbosity=2

# Coverage (si installé)
pytest --cov=factures --cov=caisse --cov=produits
```

### Tests Manuels

| Module | Test | Résultat |
|--------|------|----------|
| Dashboard | Affichage KPIs | ☐ |
| Factures | Création + Validation stock | ☐ |
| Caisse | Opérations caisse | ☐ |
| Approvisionnements | Création + Résultats | ☐ |
| Rapports | Génération PDF | ☐ |
| Boutique | Navigation + Panier | ☐ |

### Validation Métier

- [ ] **Direction:** Validation des KPIs dashboard
- [ ] **Comptabilité:** Validation des exports comptables
- [ ] **Magasin:** Validation des opérations caisse
- [ ] **IT:** Validation technique (logs, performance)

---

## ⚠️  ROLLBACK

### En Cas de Problème

```bash
# 1. Exécuter le script de rollback
python3 scripts/rollback_v2_to_v1.py

# 2. Sélectionner le backup à restaurer
# (Le script affiche la liste des backups disponibles)

# 3. Confirmer le rollback
# (Le script demande confirmation)

# 4. Vérifier le fonctionnement
python3 manage.py test
python3 manage.py runserver
```

### Rollback Manuel (si nécessaire)

```bash
# 1. Restaurer la base de données
pg_restore -U postgres -d esm --clean backups/esm_v1_backup_YYYYMMDD_database.dump

# 2. Restaurer les media
tar -xzf backups/esm_v1_backup_YYYYMMDD_media.tar.gz

# 3. Restaurer la config
tar -xzf backups/esm_v1_backup_YYYYMMDD_config.tar.gz

# 4. Checkout Git
git checkout v1.0.0_backup_YYYYMMDD

# 5. Réinstaller les dépendances v1.0
pip install -r requirements_v1.txt
```

---

## ❓ FAQ

### Q: Combien de temps dure la migration ?

**R:** Environ 30-60 minutes selon la taille de la base de données.

### Q: Y a-t-il de l'arrêt de service ?

**R:** Oui, prévoir 15-30 minutes d'indisponibilité.

### Q: Que faire si les tests échouent ?

**R:** 
1. Ne pas poursuivre la migration
2. Exécuter le rollback
3. Analyser les erreurs
4. Corriger et re-tester

### Q: Peut-on migrer sans backup ?

**R:** NON. C'est strictement interdit. Le backup est obligatoire.

### Q: Comment vérifier que la migration a réussi ?

**R:** 
- Tous les tests passent
- Validation métier OK
- Performance acceptable
- Aucune erreur dans les logs

---

## 📞 SUPPORT

### En Cas de Problème

1. **Consulter la documentation:**
   - `MIGRATION_PLAN_v2.0.md`
   - `MIGRATION_V2_PROGRESS.md`
   - `compatibility_report_*.md`

2. **Vérifier les logs:**
   ```bash
   tail -f logs/django.log
   ```

3. **Exécuter les diagnostics:**
   ```bash
   python3 scripts/test_django60_compatibility.py
   ```

4. **Effectuer un rollback si nécessaire:**
   ```bash
   python3 scripts/rollback_v2_to_v1.py
   ```

---

## 📝 CHECKLIST FINALE

### Avant Migration
- [ ] Backup effectué et vérifié
- [ ] Tests de compatibilité passés
- [ ] Environnement de test validé
- [ ] Équipe informée de l'arrêt de service
- [ ] Procédure de rollback testée

### Pendant Migration
- [ ] Migration du code effectuée
- [ ] Migrations Django appliquées
- [ ] Tests de régression passés
- [ ] Validation fonctionnelle OK

### Après Migration
- [ ] Tests métier validés
- [ ] Performance vérifiée
- [ ] Monitoring actif
- [ ] Documentation mise à jour
- [ ] Équipe formée

---

## 🎯 CRITÈRES DE SUCCÈS

La migration est considérée comme réussie si :

1. ✅ **Tous les tests passent** (100%)
2. ✅ **Validation métier OK** (tous les modules)
3. ✅ **Performance acceptable** (< 2s par page)
4. ✅ **Aucune erreur critique** dans les logs
5. ✅ **Rollback testé et fonctionnel**

---

**Dernière mise à jour:** 29/06/2026  
**Prochaine révision:** Après migration complète  
**Responsable:** [À définir]