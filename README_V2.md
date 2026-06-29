# 🚀 CONBUSCA v2.0 - Migration Guide

**Branche:** `release/v2.0`  
**Date:** 29 Juin 2026  
**Statut:** ✅ Prêt pour migration

---

## 📋 Vue d'ensemble

Cette branche contient tous les préparatifs pour la migration CONBUSCA v1.0 → v2.0.

### Changements principaux:
- ✅ Tests TDD validation stock par lots (7 tests, 100% passants)
- ✅ Infrastructure de migration complète
- ✅ Documentation exhaustive
- ✅ Scripts d'automatisation (backup, migration, rollback)
- ✅ Tests de compatibilité Django 6.0

---

## 🎯 Démarrage Rapide

### 1. Vérifier la compatibilité

```bash
python3 scripts/test_django60_compatibility.py
```

### 2. Créer un backup

```bash
chmod +x scripts/backup_v1.sh
./scripts/backup_v1.sh
```

### 3. Migrer vers v2.0

```bash
# Suivre le guide complet
cat docs/GUIDE_MIGRATION_V2.md

# Ou exécuter le script de migration
python3 scripts/migrate_v1_to_v2.py
```

### 4. En cas de problème

```bash
# Rollback automatique
python3 scripts/rollback_v2_to_v1.py

# Ou rollback manuel (voir GUIDE_MIGRATION_V2.md)
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `docs/GUIDE_MIGRATION_V2.md` | Guide pas-à-pas de migration |
| `MIGRATION_V2_PROGRESS.md` | Suivi de progression détaillé |
| `docs/SYNTHESE_FINALISATION_V2.md` | Synthèse des livrables |
| `MIGRATION_PLAN_v2.0.md` | Plan de migration original |

---

## 🧪 Tests

```bash
# Tests TDD validation stock
python3 manage.py test factures.tests.test_validation_stock_lots -v 2

# Tous les tests
python3 manage.py test --verbosity=2
```

---

## 📦 Livrables

### Code
- ✅ 7 tests TDD (100% passants)
- ✅ Migration base de données (0014)
- ✅ Logique métier (FIFO, validation stock)

### Scripts
- ✅ `scripts/backup_v1.sh` - Sauvegarde complète
- ✅ `scripts/migrate_v1_to_v2.py` - Migration données
- ✅ `scripts/test_django60_compatibility.py` - Tests compatibilité
- ✅ `scripts/rollback_v2_to_v1.py` - Rollback d'urgence

### Documentation
- ✅ Guide de migration complet
- ✅ Procédures de rollback
- ✅ Checklist de validation
- ✅ FAQ

---

## ⚠️  Important

**Cette migration nécessite:**
1. Backup complet (OBLIGATOIRE)
2. Tests de compatibilité (OBLIGATOIRE)
3. Environnement de test (RECOMMANDÉ)
4. Arrêt de service (15-30 min)

**Ne jamais migrer en production sans:**
- ✅ Backup vérifié
- ✅ Tests passés
- ✅ Rollback testé
- ✅ Validation métier

---

## 🎯 Prochaines étapes

1. **Tester le backup** sur environnement de test
2. **Vérifier la compatibilité** Django 6.0
3. **Corriger les settings** manquants
4. **Migrer Django** vers 6.0.x
5. **Tests de régression** complets
6. **Validation métier** avec utilisateurs
7. **Déploiement** staging → production

---

## 📞 Support

- **Documentation:** Voir `docs/GUIDE_MIGRATION_V2.md`
- **Problèmes:** Consulter la section FAQ du guide
- **Rollback:** `python3 scripts/rollback_v2_to_v1.py`

---

## ✅ Checklist Pré-Migration

- [ ] Backup créé et vérifié
- [ ] Tests de compatibilité passés
- [ ] Settings manquants corrigés
- [ ] Environnement de test prêt
- [ ] Équipe informée
- [ ] Rollback testé
- [ ] Validation métier planifiée

---

**Branche:** `release/v2.0`  
**Commit:** `c0dd066`  
**Prêt pour:** Migration Django 6.0

---

*Finalisé le 29 Juin 2026 par Cline (AI Assistant)*