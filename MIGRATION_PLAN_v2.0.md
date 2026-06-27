# 📋 PLAN DE MIGRATION VERSION 2.0

**Date :** 27 Juin 2026  
**Version actuelle :** 1.0.0  
**Version cible :** 2.0.0  
**Statut :** En préparation

---

## 🎯 OBJECTIFS DE LA VERSION 2.0

### 1. **Montée de version Django**
- Django 5.2.1 → 6.0.x (LTS)
- Mise à jour des dépendances
- Amélioration de la sécurité

### 2. **Refonte Architecture**
- Séparation claire des responsabilités
- Introduction d'une couche API REST
- Amélioration de la maintenabilité

### 3. **Nouvelles Fonctionnalités Majeures**
- Multi-sociétés (si applicable)
- Système de permissions avancé
- Audit trail complet
- Notifications en temps réel

---

## 📊 ÉTAT DES LIEUX ACTUEL

### **Stack Technique**
```
Django: 5.2.1
Python: 3.12.3
Base de données: PostgreSQL
Frontend: Bootstrap 3 + jQuery
API: Aucune (monolithique)
```

### **Applications (15)**
1. activity_logs - Journal d'activités
2. approvisionnements - Gestion des approvisionnements
3. caisse - Gestion des caisses
4. clients - Gestion clients
5. commandes - Gestion commandes
6. creanciers - Gestion créanciers/débiteurs
7. factures - Facturation
8. fournisseurs - Gestion fournisseurs
9. paie - Gestion paie
10. parametres - Paramètres système
11. patrimoine - Gestion patrimoine (FR, FP)
12. produits - Gestion produits/stocks
13. rapports - Reporting
14. users - Utilisateurs
15. users_management - Gestion utilisateurs

### **Fonctionnalités Clés**
- ✅ Double devise (FC/USD)
- ✅ Système de snapshots patrimoine
- ✅ Dashboard avec 8 widgets
- ✅ Gestion des caisses avec clôture journalière
- ✅ Facturation complète
- ✅ Approvisionnements avec résultats
- ✅ Paie avec bulletins
- ✅ Rapports PDF

### **Migrations (patrimoine uniquement)**
```
0001_initial.py
0002_resultatjournalier_resultatapprovisionnementsnapshot_and_more.py
0003_rename_cout_total_resultatapprovisionnementsnapshot_cout_achat_and_more.py
0004_add_fonds_roulement_snapshot.py
0005_fondsroulement_validation.py
0006_fondsroulementsnapshot_ej_usd_and_more.py
0007_resultatapprovisionnementsnapshot_chiffre_affaires_usd_and_more.py
0008_snapshotjournalier_solde_fermeture_usd.py
```

---

## ⚠️ POINTS DE RUPTURE IDENTIFIÉS

### **1. Double Devise (USD/FC)**
- **Risque :** Haut
- **Impact :** Toutes les conversions USD
- **Solution :** Maintenir la compatibilité, ajouter tests

### **2. Snapshots Patrimoine**
- **Risque :** Moyen
- **Impact :** Données historiques FR
- **Solution :** Script de migration + validation

### **3. Relations Inter-Apps**
- **Risque :** Moyen
- **Impact :** Foreign keys, imports
- **Solution :** Vérifier toutes les dépendances

### **4. Templates**
- **Risque :** Faible
- **Impact :** Extends, blocks, tags
- **Solution :** Tests de rendu automatisés

### **5. JavaScript/jQuery**
- **Risque :** Faible
- **Impact :** Charts, datepickers
- **Solution :** Vérifier compatibilité Bootstrap

---

## 🎯 STRATÉGIE DE MIGRATION

### **Approche : Progressive avec Branche Dédiée**

```
main (production)
  └── release/v2.0 (nouvelle version)
        ├── feature/api-rest
        ├── feature/multi-societes
        ├── feature/permissions-avancees
        └── hotfix/bugs
```

### **Phases de Migration**

#### **Phase 1 : Préparation (Semaine 1)**
- [x] Audit complet du projet
- [ ] Création branche `release/v2.0`
- [ ] Mise à jour requirements.txt
- [ ] Tests de compatibilité Django 6.0
- [ ] Documentation de l'architecture

#### **Phase 2 : Migration Core (Semaine 2-3)**
- [ ] Migration Django 5.2 → 6.0
- [ ] Mise à jour settings.py
- [ ] Tests unitaires
- [ ] Correction des dépréciations

#### **Phase 3 : Nouvelles Fonctionnalités (Semaine 4-6)**
- [ ] API REST (Django REST Framework)
- [ ] Multi-sociétés (si besoin)
- [ ] Permissions avancées
- [ ] Notifications temps réel

#### **Phase 4 : Tests & Validation (Semaine 7)**
- [ ] Tests d'intégration
- [ ] Tests de charge
- [ ] Recette utilisateur
- [ ] Documentation utilisateur

#### **Phase 5 : Déploiement (Semaine 8)**
- [ ] Sauvegarde complète
- [ ] Migration base de données
- [ ] Déploiement staging
- [ ] Validation métier
- [ ] Déploiement production
- [ ] Monitoring post-déploiement

---

## 🛠️ ACTIONS IMMÉDIATES

### **1. Créer la structure de versionnement**
```bash
git checkout -b release/v2.0
git push -u origin release/v2.0
```

### **2. Mettre à jour requirements.txt**
```
# Core
Django==6.0.x
djangorestframework==3.15.x
django-filter==24.x

# Frontend (migration vers moderne)
# Option A: Garder Bootstrap 3 (compatibilité)
# Option B: Migrer vers Bootstrap 5

# Tests
pytest==8.x
pytest-django==4.18.x
```

### **3. Créer les scripts de migration**
- `scripts/migrate_v1_to_v2.py` - Migration données
- `scripts/backup_v1.py` - Sauvegarde pré-migration
- `scripts/rollback_v2_to_v1.py` - Rollback si nécessaire

### **4. Préparer les tests**
- Tests de régression automatiques
- Tests de compatibilité devise
- Tests de migration des snapshots

---

## 📋 CHECKLIST PRÉ-DÉPLOIEMENT

### **Technique**
- [ ] Sauvegarde complète de la base de données
- [ ] Sauvegarde des fichiers media
- [ ] Sauvegarde du code (git tag v1.0.0)
- [ ] Environnement de test isolé
- [ ] Scripts de rollback testés

### **Fonctionnel**
- [ ] Tests de régression passés
- [ ] Validation des conversions USD/FC
- [ ] Validation des snapshots patrimoine
- [ ] Validation des exports PDF
- [ ] Validation du dashboard

### **Documentation**
- [ ] Guide de migration rédigé
- [ ] Changelog complet
- [ ] Documentation API (si applicable)
- [ ] Notes de version
- [ ] Procédure de rollback

---

## 🚀 PROCHAINES ÉTAPES

**Immédiat :**
1. Créer la branche `release/v2.0`
2. Mettre à jour requirements.txt
3. Créer l'environnement de test
4. Commencer la migration Django

**Cette semaine :**
1. Finaliser l'audit complet
2. Tester la compatibilité Django 6.0
3. Identifier tous les breaking changes
4. Préparer les scripts de migration

---

## 📞 CONTACTS & RESPONSABILITÉS

- **Chef de projet :** [À définir]
- **Lead technique :** [À définir]
- **Tests & Validation :** [À définir]
- **Base de données :** [À définir]

---

## 📝 NOTES

- Ce document est vivant et sera mis à jour régulièrement
- Toutes les modifications doivent être tracées dans git
- Prévoir un rollback à chaque étape critique
- Tester systématiquement sur environnement isolé avant production

**Dernière mise à jour :** 27/06/2026