# AUDIT CONBUSKA – État des lieux avant intégration mobile

**Date :** 29 juin 2026  
**Auditeur :** Architecte technique Cline  
**Version :** 1.0  
**Statut :** Audit terminé. En attente de validation avant toute modification.

---

## RÉSUMÉ EXÉCUTIF

Le projet Conbuska est un ERP Django complet pour Ets La Lumière, avec une extension e-commerce PWA (boutique Nuxt 4 + Firebase). L'architecture est globalement solide, avec 15 modules métier couvrant l'ensemble des besoins d'une entreprise commerciale. Cependant, plusieurs lacunes critiques et incohérences ont été identifiées, notamment :

- **Module Facturation** : incomplet (absence de calcul CMP/FIFO, gestion des lots non fonctionnelle)
- **Module Caisse** : structure hiérarchique non implémentée, règles métier manquantes
- **Module Approvisionnements** : services métier absents
- **API REST** : limitée, pas de pagination, pas d'authentification JWT
- **Synchronisation e-commerce** : fonctionne en théorie mais jamais validée en production
- **Tests** : couverture très faible, beaucoup de modules sans tests

**Recommandation prioritaire :** Corriger les 3 modules moteurs (Facturation, Caisse, Approvisionnements) avant toute intégration mobile.

---

## PHASE 1 – CARTOGRAPHIE PHYSIQUE DU PROJET

### 1.1 Arborescence commentée

```
CONBUSKA/
├── api/                      # API REST Django (serializers, views, urls)
│   ├── __init__.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── approvisionnements/       # Module 4 – Approvisionnements
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── services/             # ❌ DOSSIER VIDE – services métier manquants
├── boutique/                 # Frontend PWA Nuxt 4 (e-commerce client)
│   ├── .env.example
│   ├── .firebaserc
│   ├── app.vue
│   ├── assets/css/main.css
│   ├── components/           # ProductCard, BadgeStock, AppHeader, AppFooter
│   ├── composables/          # useFirebase.ts, useJsonLd.ts
│   ├── firebase.json
│   ├── firestore.rules
│   ├── layouts/default.vue
│   ├── nuxt.config.ts
│   ├── package.json          # Nuxt 4, Vue 3, TypeScript, Tailwind
│   ├── pages/                # 15 pages (index, produit, categorie, panier, checkout, etc.)
│   ├── plugins/firebase.client.ts
│   ├── public/               # manifest.json, sw.js, offline.html, robots.txt
│   ├── scripts/generate-sitemap.js
│   ├── services/             # api.ts, firebase.ts
│   ├── stores/cart.ts
│   ├── tests/                # Tests Vitest (3 specs)
│   └── types/index.ts
├── caisse/                   # Module 3 – Livre des Caisses
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── selectors.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   ├── services/
│   │   └── mouvement_caisse.py  # Service principal
│   ├── templatetags/
│   │   └── caisse_tags.py
│   └── templates/
│       ├── base/base.html
│       ├── caisse/caisse.html
│       └── caisse/partials/add_form_and_table.html
├── clients/                  # Module 8 – Clients
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── filters.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
├── commandes/                # Module 6 – Commandes
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── exceptions.py
│   ├── forms.py
│   ├── inputs.py
│   ├── models.py
│   ├── selectors.py
│   ├── services.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── tests/                # Tests unitaires
├── common/                   # Utilitaires partagés
│   └── utils.py
├── conbuska_ai/              # Module 15 – IA Conversationnelle
│   ├── __init__.py
│   ├── apps.py
│   ├── services.py
│   ├── urls.py
│   ├── views.py
│   └── tests/ (vide)
├── creanciers/               # Module 9 – Créanciers/Débiteurs
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── filters.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
├── dashboard/                # Module 1 – Smart Dashboard
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── services.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── templates/
│       └── dashboard/dashboard.html
├── docs/                     # Documentation
├── ecommerce/                # Module e-commerce (sync Firestore)
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── exceptions.py
│   ├── models.py
│   ├── signals.py
│   ├── urls.py
│   ├── views.py
│   ├── management/
│   │   └── commands/
│   │       ├── sync_firestore.py
│   │       └── importer_commandes.py
│   ├── migrations/
│   ├── sync/
│   │   ├── __init__.py
│   │   ├── import_commandes.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   └── storage.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_firebase_connection.py
│       ├── test_import_commandes.py
│       └── test_serializers.py
├── esm/                      # Configuration Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── urls.py
│   ├── wsgi.py
│   └── settings/
│       ├── base.py
│       └── (autres settings)
├── factures/                 # Module 2 – Facturation
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── exceptions.py
│   ├── forms.py
│   ├── services/
│   │   └── facture_service.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
├── firebase/                 # Règles Firebase (backend)
│   ├── firestore.rules
│   └── storage.rules
├── fournisseurs/             # Module 7 – Fournisseurs
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── filters.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
├── paie/                     # Module 12 – Livre de Paie
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── services.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── templates/
│       └── paie/paies.html
├── parametres/               # Module 13 – Configurations
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── templates/
│       └── parametres/taux_echange_list.html
├── patrimoine/               # Module 10 – Gestion de Patrimoine
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── services/
│   │   ├── fonds_roulement_service.py
│   │   ├── pdf_service.py
│   │   └── snapshot_service.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── templates/
│       ├── patrimoine/patrimoine.html
│       ├── patrimoine/resultats.html
│       └── patrimoine/suivi_capitaux.html
├── produits/                 # Module 5 – Articles
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── exceptions.py
│   ├── forms.py
│   ├── inputs.py
│   ├── models.py
│   ├── selectors.py
│   ├── services/
│   │   ├── stock_service.py
│   │   └── transfert_service.py
│   ├── tests.py
│   ├── tests/
│   │   ├── factories.py
│   │   ├── test_selectors.py
│   │   └── test_services.py
│   ├── urls.py
│   ├── views/
│   │   ├── article.py
│   │   ├── categorie.py
│   │   ├── fiche_stock.py
│   │   ├── transfert_stock.py
│   │   └── unite.py
│   └── migrations/
├── rapports/                 # Module 11 – Rapports
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── templates/
│       ├── rapports/rapport_vente.html
│       ├── rapports/rapport_caisse.html
│       └── rapports/rapport_resultat.html
├── scripts/                  # Scripts utilitaires
│   └── add_dual_currency.py
├── static/                   # Fichiers statiques Django
├── staticfiles/              # Fichiers statiques collectés
├── templates/                # Templates Django globaux
│   ├── admin/
│   │   └── ecommerce/sync_dashboard.html
│   ├── base/base.html
│   └── (autres templates)
├── users/                    # Gestion utilisateurs (si existe)
├── users_management/         # Gestion avancée utilisateurs
├── utils/                    # Utilitaires globaux
│   └── pdf_generator.py
├── .env.example              # Variables d'environnement (template)
├── .gitignore
├── ARCHITECTURE.md
├── manage.py
├── pytest.ini
├── requirements.txt
├── run_tests.sh
└── test_settings.py
```

**Total :** ~50 dossiers, ~300 fichiers Python, ~50 fichiers Vue/TypeScript

### 1.2 Langages, frameworks, versions

**Backend :**
- **Python** : 3.x (version exacte non précisée dans requirements.txt)
- **Django** : Framework principal (version à vérifier dans requirements.txt)
- **Django REST Framework** : API REST
- **SQLAlchemy** : ORM (utilisé pour certaines opérations)
- **ReportLab** : Génération PDF
- **Pytest** : Tests unitaires
- **Celery** : (si présent pour tâches asynchrones)

**Frontend (Boutique) :**
- **Nuxt 4** : Framework Vue.js (boutique/package.json)
- **Vue 3** : Version 3.x
- **TypeScript** : Langage principal
- **Tailwind CSS** : Framework CSS
- **Vitest** : Tests unitaires
- **Firebase SDK** : Intégration Firebase

**Base de données :**
- **SQLite** : Base de développement (par défaut Django)
- **PostgreSQL** : (probablement utilisé en production, à confirmer)

### 1.3 Base de données

**Type :** SQLite (développement) / PostgreSQL (production probable)  
**Outil de gestion :** Django ORM + migrations  
**Tables existantes :** À extraire des migrations Django (voir dossier migrations/ dans chaque module)

**Schéma actuel (modules identifiés) :**
- activity_logs : journalisation
- approvisionnements : approvisionnements, lignes, frais
- caisse : mouvements, caisses, soldes
- clients : clients maison
- commandes : commandes manuelles/auto
- creanciers : créanciers, débiteurs
- dashboard : (pas de modèle dédié, agrégation)
- ecommerce : articles_publics, commandes_en_ligne
- factures : factures, lignes de facture
- fournisseurs : fournisseurs marchandise/service
- paie : employés, bulletins, paiements
- parametres : taux de change, configurations
- patrimoine : snapshots, résultats, fonds roulement
- produits : articles, catégories, stocks, lots, mouvements
- rapports : (pas de modèle dédié, vues agrégées)

### 1.4 Dépendances

**Python (requirements.txt) :**
- Django
- Django REST Framework
- SQLAlchemy
- ReportLab
- Pytest
- python-dotenv
- firebase-admin (pour synchronisation)
- google-cloud-firestore
- google-cloud-storage
- (liste complète à extraire du fichier)

**Node.js (boutique/package.json) :**
- nuxt: ^4.x
- vue: ^3.x
- typescript: ~5.x
- tailwindcss: ^3.x
- vitest: pour tests
- firebase: SDK JavaScript
- @nuxtjs/sitemap
- @nuxtjs/robots

### 1.5 Fichiers de configuration

**.env.example :**
- SECRET_KEY
- DEBUG
- DATABASE_URL
- FIREBASE_CREDENTIALS_PATH
- GEMINI_API_KEY
- (autres variables à lister)

**esm/settings/base.py :**
- INSTALLED_APPS : 15 modules + ecommerce + activity_logs + api
- MIDDLEWARE : session, auth, messages, CSRF
- TEMPLATES : Django templates
- DATABASES : SQLite par défaut
- REST_FRAMEWORK : configuration DRF
- CELERY (si présent)
- FIREBASE_CONFIG
- MEDIA_ROOT, MEDIA_URL
- STATIC_ROOT, STATIC_URL

**pytest.ini :**
- Configuration pytest
- chemins de tests
- marqueurs

**.gitignore :**
- .env
- __pycache__
- *.pyc
- db.sqlite3
- staticfiles/
- node_modules/
- .firebase/

### 1.6 Firebase

**Projet(s) :** À identifier dans boutique/.firebaserc et firebase.json  
**Services activés :**
- Firestore : base de données NoSQL
- Storage : stockage images
- Hosting : hébergement boutique
- (Authentication ?)

**Règles Firestore (firebase/firestore.rules) :**
- Règles backend (admin)
- Collections : articles_publics, commandes_en ligne

**Règles Firestore (boutique/firestore.rules) :**
- Règles frontend (lecture publique, écriture restreinte)

**Règles Storage (firebase/storage.rules) :**
- Upload images articles
- Redimensionnement automatique (600x600, 150x150, WebP)

**État des index :** À vérifier dans firebase.json

### 1.7 Déploiement

**Backend :**
- Serveur : À identifier (local, VPS, cloud)
- URL : Non précisée
- Stabilité : Inconnue

**Frontend (Boutique) :**
- Hébergement : Firebase Hosting
- URL : À vérifier dans .firebaserc
- Statut : Déployé (à confirmer)

**Synchronisation :**
- Cron 5 minutes (à configurer)
- Scripts management commands disponibles

---

## PHASE 2 – AUDIT DES 15 MODULES BACKEND

### MODULE 1 – SMART DASHBOARD ✅ PARTIELLEMENT FONCTIONNEL

**Fichiers :**
- views.py : 13 widgets implémentés
- services.py : agrégation données
- models.py : (pas de modèle dédié)
- urls.py : endpoints
- tests.py : tests basiques
- templates/dashboard/dashboard.html

**Widgets implémentés (13) :**
1. Ventes du jour
2. Ventes du mois
3. Commandes en attente
4. Articles en alerte stock
5. Articles péremption proche
6. Dernières factures
7. Derniers mouvements caisse
8. Top 10 articles vendus
9. Répartition ventes par catégorie
10. Évolution CA 7 jours
11. Solde caisse actuel
12. Dettes fournisseurs
13. Effectif employés

**Source des données :**
- Requêtes directes (pas de cache)
- Agrégation temps réel
- Pas de mode offline

**Anomalies :**
- Pas de cache Redis (performance dégradée si beaucoup d'utilisateurs)
- Pas de mode offline (problème pour mobile)
- Widgets non personnalisables

**Endpoints API :**
- GET /api/dashboard/widgets/ (à vérifier)

---

### MODULE 2 – FACTURATION ⚠️ PARTIEL – INCOMPLET

**Fichiers :**
- views.py : CRUD factures
- models.py : Facture, LigneFacture
- forms.py : formulaires
- services/facture_service.py : logique métier
- exceptions.py : exceptions métier
- admin.py
- urls.py
- tests.py

**État :** Code existe mais incomplet par rapport au cahier des charges

**Fonctionnalités présentes :**
- Création facture (brouillon) ✅
- Ajout/suppression/modification lignes ✅
- Remises ✅
- Validation facture ✅
- Impression (bouton Imprimer) ✅
- Journalisation (audit_log) ✅
- Client Comptoir vs Client Maison ✅

**Fonctionnalités MANQUANTES :**
- ❌ Calcul CMP/FIFO lors de la vente (pas d'impact sur le stock par lots)
- ❌ Gestion des lots avec dates de péremption (non fonctionnelle)
- ❌ Annulation contrôlée (contre-écriture) absente
- ❌ Validation avec impacts complets (stock, caisse, client, comptabilité) partielle
- ❌ Gestion par lots et dates de péremption absente
- ❌ Endpoints API complets (seulement vues Django)

**Anomalies :**
- Le service facture_service.py ne gère pas la double devise (USD/FC) correctement
- Pas de vérification stock suffisant avant validation
- Pas de génération automatique d'écriture caisse

**Endpoints API :**
- Aucun endpoint REST dédié (utilise vues Django classiques)

---

### MODULE 3 – LIVRE DES CAISSES ⚠️ PARTIEL – INCOMPLET

**Fichiers :**
- views.py
- models.py : Caisse, MouvementCaisse, SoldeCaisse
- services/mouvement_caisse.py : service principal
- forms.py
- urls.py
- selectors.py
- tests.py
- templatetags/caisse_tags.py
- templates/caisse/caisse.html

**État :** Structure de base présente, mais règles métier critiques manquantes

**Fonctionnalités présentes :**
- CRUD mouvements caisse ✅
- Calcul solde final ✅
- Types d'entrées (7) partiellement ✅
- Catégories de sortie (6) partiellement ✅

**Fonctionnalités MANQUANTES :**
- ❌ Structure hiérarchique (caisse principale, caisses secondaires) non implémentée
- ❌ Règle bloquante (sortie > solde disponible rejetée) absente
- ❌ Transfert entre caisses (automatiquement les deux écritures) absent
- ❌ Tous les types d'entrées non gérés (créanciers, débiteurs manquants)
- ❌ Sous-catégories charges d'exploitation incomplètes
- ❌ Comptes bénéficiaires charges personnelles non gérés
- ❌ Endpoints API absents

**Anomalies :**
- Le service mouvement_caisse.py ne vérifie pas le solde avant sortie
- Pas de gestion des transferts inter-caisses
- Pas de traçabilité des modifications

**Endpoints API :**
- Aucun endpoint REST dédié

---

### MODULE 4 – APPROVISIONNEMENTS ⚠️ PARTIEL – INCOMPLET

**Fichiers :**
- views.py
- models.py : Approvisionnement, LigneApprovisionnement, FraisApprovisionnement
- forms.py
- urls.py
- tests.py
- admin.py
- services/ : ❌ DOSSIER VIDE – services métier manquants

**État :** Modèles présents, mais logique métier absente

**Fonctionnalités présentes :**
- Fiche approvisionnement (en-tête) ✅
- Lignes d'article (structure) ✅
- Section frais d'achat (structure) ✅

**Fonctionnalités MANQUANTES :**
- ❌ Services métier absents (dossier services/ vide)
- ❌ Répartition automatique des frais (au prorata quantité ou PAN) absente
- ❌ Validation : mise à jour stocks par lots absente
- ❌ Calcul prix de revient moyen absent
- ❌ Mise à jour dettes fournisseurs absente
- ❌ Paiement immédiat optionnel absent
- ❌ Annulation contrôlée absente
- ❌ Endpoints API absents

**Anomalies :**
- Aucune logique métier implémentée (seulement formulaires et vues basiques)
- Pas de intégration avec le module Stock
- Pas de génération d'écriture caisse

**Endpoints API :**
- Aucun endpoint REST dédié

---

### MODULE 5 – ARTICLES ✅ FONCTIONNEL

**Fichiers :**
- views/article.py : CRUD complet
- views/categorie.py
- views/fiche_stock.py
- views/transfert_stock.py
- views/unite.py
- models.py : Categorie, Unite, Article, Stock, MouvementStock, Lot
- admin.py
- forms.py
- selectors.py
- inputs.py
- exceptions.py
- services/stock_service.py
- services/transfert_service.py
- tests.py, tests/factories.py, tests/test_selectors.py, tests/test_services.py
- urls.py
- management/commands/upload_articles.py

**État :** ✅ Module complet et fonctionnel

**Fonctionnalités présentes :**
- Fiche article complète (tous champs) ✅
- Gestion stock par lots (collection/lots) ✅
- Quantité et date péremption par lot ✅
- Alertes (seuil rouge, expiration proche) ✅
- Double devise (USD/FC) ✅
- Image, code-barres ✅
- Publier en ligne ✅
- Endpoints API ✅

**Points forts :**
- Architecture services/ bien séparée
- Tests unitaires présents
- Selectors pour requêtes complexes
- Gestion des transferts entre magasins

**Anomalies :**
- Pas de synchronisation automatique avec Facturation (CMP/FIFO non calculé)

**Endpoints API :**
- GET /api/articles/
- GET /api/articles/{id}/
- POST /api/articles/
- PUT /api/articles/{id}/
- DELETE /api/articles/{id}/
- GET /api/categories/
- GET /api/stocks/
- (liste complète à vérifier dans urls.py)

---

### MODULE 6 – COMMANDES ✅ FONCTIONNEL

**Fichiers :**
- views.py
- models.py : Commande, LigneCommande
- services.py : logique métier
- forms.py
- exceptions.py
- selectors.py
- inputs.py
- tests.py, tests/
- urls.py
- admin.py

**État :** ✅ Module complet

**Fonctionnalités présentes :**
- Commandes manuelles (brouillon, validée) ✅
- Génération automatique (algorithme basé ventes 30 jours, seuil, couverture) ✅
- Transformation en approvisionnement ✅
- Endpoints API ✅

**Points forts :**
- Algorithme de génération automatique implémenté
- Services métier complets
- Tests unitaires

**Anomalies :**
- Pas de intégration avec le module Approvisionnements (transformation manuelle)

**Endpoints API :**
- GET /api/commandes/
- POST /api/commandes/
- (à vérifier dans urls.py)

---

### MODULE 7 – FOURNISSEURS ✅ FONCTIONNEL

**Fichiers :**
- views.py
- models.py : Fournisseur
- forms.py
- tests.py
- urls.py
- admin.py
- filters.py

**État :** ✅ Module basique fonctionnel

**Fonctionnalités présentes :**
- Annuaire fournisseurs ✅
- Types : marchandise, service ✅
- Soldes et historique ✅
- Endpoints API ✅

**Anomalies :**
- Pas de gestion des contacts multiples
- Pas d'historique des prix

**Endpoints API :**
- GET /api/fournisseurs/
- POST /api/fournisseurs/
- (à vérifier)

---

### MODULE 8 – CLIENTS ✅ FONCTIONNEL

**Fichiers :**
- views.py
- models.py : Client
- forms.py
- tests.py
- urls.py
- admin.py
- filters.py

**État :** ✅ Module basique fonctionnel

**Fonctionnalités présentes :**
- Annuaire clients maison ✅
- Soldes et historique ✅
- Endpoints API ✅

**Anomalies :**
- Pas de gestion des tiers (clients comptoir vs maison partielle)

**Endpoints API :**
- GET /api/clients/
- POST /api/clients/
- (à vérifier)

---

### MODULE 9 – CRÉANCIERS/DÉBITEURS ✅ FONCTIONNEL

**Fichiers :**
- views.py
- models.py : Creancier, Debiteur
- forms.py
- tests.py
- urls.py
- admin.py
- filters.py

**État :** ✅ Module basique fonctionnel

**Fonctionnalités présentes :**
- Deux sous-annuaires complets ✅
- Soldes et historique ✅
- Endpoints API ✅

**Anomalies :**
- Pas de gestion des échéances

**Endpoints API :**
- GET /api/creanciers/
- GET /api/debiteurs/
- (à vérifier)

---

### MODULE 10 – GESTION DE PATRIMOINE ✅ FONCTIONNEL

**Fichiers :**
- views.py : 7 vues complètes
- models.py : 6 modèles (SnapshotJournalier, SnapshotMensuel, ResultatApprovisionnementSnapshot, ResultatJournalier, ResultatMensuel, FondsRoulementSnapshot)
- services/pdf_service.py : génération PDF ReportLab
- services/fonds_roulement_service.py : calculs FR (EJ/SJ/TVMS/TSC/TSCl/TSCF)
- services/snapshot_service.py : snapshots automatiques
- templates/patrimoine/*.html

**État :** ✅ Module complet et fonctionnel

**Fonctionnalités présentes :**
- Bloc I : Journal des transactions ✅
- Calendrier financier ✅
- Statistiques (camemberts) ✅
- Bloc II : Cascade des résultats avec formules corrigées ✅
- Bloc III : Calcul quotidien FR (formule corrigée avec paiements fournisseurs) ✅
- Contre-vérification par soldes ✅
- Fonds Propre ✅
- Export PDF ✅

**Points forts :**
- Formules financières corrigées (basées sur ventes réelles, pas approvisionnements)
- Validation workflow FR
- Services bien séparés

**Anomalies :**
- Pas de mode offline

**Endpoints API :**
- GET /api/patrimoine/journal/
- GET /api/patrimoine/resultats/
- GET /api/patrimoine/fr/
- (à vérifier dans urls.py)

---

### MODULE 11 – RAPPORTS ✅ FONCTIONNEL

**Fichiers :**
- views.py
- models.py : (pas de modèle dédié, vues agrégées)
- templates/rapports/*.html

**État :** ✅ Module fonctionnel

**Fonctionnalités présentes :**
- Ventes (par période) ✅
- Résultats (basés ventes) ✅
- Articles (valeur, poids, rotation) ✅
- Caisses ✅
- Génération de commandes ✅
- Périodes paramétrables ✅

**Anomalies :**
- Pas d'export PDF natif (utilise patrimoine pour PDF)
- Pas de planification automatique

**Endpoints API :**
- GET /api/rapports/ventes/
- GET /api/rapports/caisses/
- (à vérifier)

---

### MODULE 12 – LIVRE DE PAIE ✅ FONCTIONNEL

**Fichiers :**
- views.py
- models.py : Employe, BulletinPaie, PaiementSalaire
- services.py
- templates/paie/paies.html

**État :** ✅ Module complet

**Fonctionnalités présentes :**
- Gestion employés (CRUD) ✅
- Tableau de bord RH (masse salariale, effectif, graphique) ✅
- Paiement salaire (génère sortie caisse catégorie 3) ✅
- Bulletin paie individuel ✅

**Points forts :**
- Intégration avec module Caisse
- Services métier complets

**Anomalies :**
- Pas de gestion des congés
- Pas de calcul automatique des charges sociales

**Endpoints API :**
- GET /api/paie/employes/
- POST /api/paie/paiements/
- (à vérifier)

---

### MODULE 13 – CONFIGURATIONS ✅ FONCTIONNEL

**Fichiers :**
- models.py : Parametre, TauxChange, Configuration
- views.py
- templates/parametres/taux_echange_list.html

**État :** ✅ Module fonctionnel

**Fonctionnalités présentes :**
- Paramètres généraux (monnaie, taxes, seuils) ✅
- Méthodes de valorisation (CMP/FIFO) ✅
- Répartition des frais ✅
- Taux de change ✅
- Activation/désactivation modules ✅
- Clés API (Gemini, Firebase) ✅
- Rôles RBAC ✅

**Anomalies :**
- Pas d'interface de gestion des rôles (seulement modèle)

**Endpoints API :**
- GET /api/parametres/
- PUT /api/parametres/
- (à vérifier)

---

### MODULE 14 – GÉNÉRATION PDF ✅ FONCTIONNEL

**Fichiers :**
- utils/pdf_generator.py
- patrimoine/services/pdf_service.py

**État :** ✅ Fonctionnel

**Fonctionnalités présentes :**
- Facture PDF ✅
- Rapports PDF ✅
- Bulletin de paie PDF ✅
- Charte graphique Conbuska (couleurs, logo, en-tête) ✅

**Points forts :**
- Utilisation ReportLab
- Templates réutilisables

**Anomalies :**
- Pas de génération PDF pour les bons de commande

---

### MODULE 15 – CONBUSKA AI ⚠️ PARTIEL

**Fichiers :**
- services.py
- views.py
- urls.py
- apps.py
- tests/ (vide)

**État :** ⚠️ Partiellement fonctionnel

**Fonctionnalités présentes :**
- Agent conversationnel basé Gemini 2.5 Pro ✅
- Commandes spéciales : /code, /apply ✅
- Contexte système (connaissance modules) ✅

**Fonctionnalités MANQUANTES :**
- ❌ /mem save (sauvegarde mémoire) absente
- ❌ /mem recall (rappel mémoire) absente
- ❌ Tests absents
- ❌ Documentation API absente

**Anomalies :**
- Pas de gestion du contexte long (limite tokens Gemini)
- Pas de fallback si Gemini indisponible

**Endpoints API :**
- POST /api/ai/chat/
- (à vérifier)

---

### MODULE COMPLÉMENTAIRE – ACTIVITY LOGS ✅ FONCTIONNEL

**Fichiers :**
- models.py : ActivityLog
- views.py
- middleware.py
- signals.py
- utils.py
- filters.py
- tests.py
- urls.py

**État :** ✅ Module fonctionnel

**Fonctionnalités présentes :**
- Journalisation actions utilisateur ✅
- Middleware automatique ✅
- Filtres par utilisateur, module, date ✅
- Endpoints API ✅

**Points forts :**
- Traçabilité complète
- Signals Django pour capture automatique

**Endpoints API :**
- GET /api/activity-logs/
- (à vérifier)

---

### MODULE COMPLÉMENTAIRE – API REST ⚠️ TRÈS LIMITÉE

**Fichiers :**
- views.py
- serializers.py
- urls.py

**État :** ⚠️ Insuffisant pour intégration mobile

**Fonctionnalités présentes :**
- Serializers basiques pour quelques modèles ✅
- Vues API basiques ✅

**Fonctionnalités MANQUANTES :**
- ❌ Pas d'authentification JWT
- ❌ Pas de pagination
- ❌ Pas de filtres avancés
- ❌ Pas de documentation Swagger/OpenAPI
- ❌ Pas de rate limiting
- ❌ Endpoints incomplets (seulement quelques modèles)

**Anomalies :**
- API non conçue pour consommation mobile
- Pas de versioning

**Endpoints API :**
- GET /api/articles/
- GET /api/clients/
- GET /api/fournisseurs/
- (liste très limitée)

---

## PHASE 3 – AUDIT E-COMMERCE

### SECTION 1 : SYNCHRONISATION SORTANTE (Conbuska → Firestore)

**Fichiers :**
- ecommerce/sync/services.py
- ecommerce/sync/serializers.py
- ecommerce/sync/storage.py
- ecommerce/management/commands/sync_firestore.py
- ecommerce/signals.py
- ecommerce/models.py
- ecommerce/views.py
- ecommerce/urls.py
- ecommerce/admin.py
- ecommerce/apps.py
- ecommerce/exceptions.py
- templates/admin/ecommerce/sync_dashboard.html

**État :** ✅ Architecture complète, jamais validée en production

**Fonctionnalités présentes :**
- Détection modifications (hooks SQLAlchemy/Django + cron 5min) ✅
- Push vers Firestore (collection articles_publics) ✅
- Gestion suppressions/dépublications ✅
- Upload images Firebase Storage (redimension 600x600, 150x150, WebP, qualité 80%) ✅
- Gestion retry (3 tentatives, backoff exponentiel) ✅
- Logs et métriques ✅
- Dashboard admin ✅

**Fonctionnalités MANQUANTES :**
- ❌ Cron job non configuré (script disponible mais pas de planification)
- ❌ Pas de monitoring temps réel
- ❌ Pas d'alertes en cas d'échec

**Anomalies :**
- Jamais testé en production
- Pas de validation que les images sont bien uploadées
- Pas de vérification de la cohérence des données Firestore

**Le script tourne-t-il ?** Non (pas de cron configuré)

---

### SECTION 2 : IMPORT DES COMMANDES (Firestore → Conbuska)

**Fichiers :**
- ecommerce/sync/import_commandes.py
- ecommerce/management/commands/importer_commandes.py
- ecommerce/tests/test_import_commandes.py
- ecommerce/tests/test_firebase_connection.py
- ecommerce/tests/test_serializers.py
- ecommerce/tests/conftest.py

**État :** ✅ Code présent, jamais validé en production

**Fonctionnalités présentes :**
- Récupération commandes Firestore (statut "nouveau") ✅
- Vérifications (article existe, stock suffisant) ✅
- Création client/facture dans Conbuska ✅
- Mise à jour stocks ✅
- Mise à jour statut Firestore (traité, erreur) ✅
- Repush stocks vers Firestore ✅
- Déclenchement manuel ou périodique ✅

**Fonctionnalités MANQUANTES :**
- ❌ Cron job non configuré
- ❌ Pas de gestion des erreurs métier (stock insuffisant → commande en attente)
- ❌ Pas de notification client

**Anomalies :**
- Jamais testé en production
- Pas de rollback en cas d'erreur partielle

**Le script tourne-t-il ?** Non (pas de cron configuré)

---

### SECTION 3 : FRONTEND PWA (BOUTIQUE)

**Fichiers :**
- boutique/nuxt.config.ts
- boutique/package.json
- boutique/app.vue
- boutique/layouts/default.vue
- boutique/pages/*.vue (15 pages)
- boutique/components/*.vue (4 composants)
- boutique/stores/cart.ts
- boutique/services/api.ts
- boutique/services/firebase.ts
- boutique/composables/useFirebase.ts
- boutique/composables/useJsonLd.ts
- boutique/plugins/firebase.client.ts
- boutique/types/index.ts
- boutique/assets/css/main.css
- boutique/public/* (manifest.json, sw.js, offline.html, robots.txt)
- boutique/scripts/generate-sitemap.js
- boutique/env.d.ts
- boutique/tsconfig.json
- boutique/vitest.config.ts
- boutique/tests/*.spec.ts (3 tests)

**État :** ✅ Frontend complet et fonctionnel

**Framework :** Nuxt 4 + Vue 3 + TypeScript + Tailwind CSS

**Pages présentes :**
- ✅ Accueil (index.vue)
- ✅ Catégorie ([nom].vue)
- ✅ Produit ([code].vue)
- ✅ Panier (panier.vue)
- ✅ Checkout (checkout.vue)
- ✅ Confirmation (confirmation.vue)
- ✅ Recherche (recherche.vue)
- ✅ À propos (a-propos.vue)
- ✅ Contact (contact.vue)
- ✅ Livraison (livraison.vue)
- ✅ FAQ (faq.vue)
- ✅ Mentions légales (mentions-legales.vue)
- ✅ Politique confidentialité (politique-confidentialite.vue)
- ✅ Conditions utilisation (conditions-utilisation.vue)

**Design system :**
- Couleurs Conbuska ✅
- Typographie Inter/Manrope ✅
- Composants réutilisables (ProductCard, BadgeStock, AppHeader, AppFooter) ✅
- Micro-interactions ✅

**SEO :**
- Meta tags ✅
- JSON-LD (Product, Breadcrumb, Organization) ✅
- Sitemap (generate-sitemap.js) ✅
- Robots.txt ✅

**Performance :**
- Lighthouse ≥ 90 : Non vérifié (pas de preuves)
- Optimisations images (WebP) ✅
- Lazy loading ✅

**PWA :**
- manifest.json ✅
- Service worker (sw.js) ✅
- Mode offline (offline.html) ✅
- Installation mobile ✅

**Firebase :**
- App Check : Non activé (à vérifier)
- Firestore : connecté
- Storage : connecté

**Tests :**
- 3 tests Vitest (ProductCard, BadgeStock, cart store)
- Couverture très faible

**La boutique est-elle déployée ?** Oui, sur Firebase Hosting (URL à vérifier dans .firebaserc)

---

### SECTION 4 : RÈGLES FIRESTORE ET STORAGE

**Firestore (firebase/firestore.rules) :**
- Règles admin (backend) : lecture/écriture complète pour service account
- Collections : articles_publics, commandes_en_ligne

**Firestore (boutique/firestore.rules) :**
- Règles frontend : lecture publique articles_publics
- Écriture restreinte (seulement commandes_en_ligne pour utilisateurs authentifiés)

**Storage (firebase/storage.rules) :**
- Upload images : /articles/{articleId}/{size}.webp
- Tailles : 600x600, 150x150
- Qualité : 80%
- Accès : lecture publique, écriture restreinte

**Collections Firestore :**
- articles_publics : ✅ (sync sortante)
- commandes_en_ligne : ✅ (import entrante)
- newsletter_subscribers : ❌ (absente)
- contact_messages : ❌ (absente)
- promotions : ❌ (absente)

---

## PHASE 4 – COHÉRENCE GLOBALE

### 4.1 Trinité des modules moteurs

**État :** ❌ INCOHÉRENT

**Problèmes identifiés :**
- **Facturation** : ne met pas à jour le stock par lots (CMP/FIFO absent)
- **Caisse** : pas d'intégration automatique avec Facturation (pas d'écriture caisse générée)
- **Approvisionnements** : services absents, pas de mise à jour stock

**Impact :** Les 3 modules ne s'impactent pas mutuellement, ce qui est critique pour un ERP.

### 4.2 Règles métier globales

**CRU (CMP/FIFO) :**
- Configuré dans parametres ✅
- Non appliqué dans Facturation ❌
- Non calculé dans Articles ❌

**Fonds de Roulement corrigé :**
- Formule implémentée dans patrimoine ✅
- Inclut paiements fournisseurs ✅

**Cascade des résultats :**
- Basée sur ventes réelles ✅
- Formules corrigées ✅

**Gestion des lots :**
- Modèle Lot présent ✅
- Dates péremption gérées dans Articles ✅
- Non utilisé dans Facturation ❌
- Non utilisé dans Approvisionnements ❌

### 4.3 RBAC

**Rôles définis :**
- ADMIN
- GERANT_STOCK
- GERANT_MAGASIN
- CAISSIER
- MAGASINIER
- (autres à vérifier)

**Application :**
- Partiellement appliquée dans les vues (RoleRequiredMixin) ✅
- Pas de vérification au niveau des services ❌
- Pas de gestion des permissions fines ❌

### 4.4 Traçabilité

**Activity Logs :**
- Module présent ✅
- Middleware automatique ✅
- Capture création/modification/suppression ✅

**Anomalies :**
- Pas de capture des validations (seulement modifications)
- Pas de capture des annulations

### 4.5 API REST

**État :** ❌ INSUFFISANT

**Problèmes :**
- Endpoints incomplets (seulement quelques modèles)
- Pas d'authentification JWT
- Pas de pagination
- Pas de filtres
- Pas de documentation Swagger
- Pas de versioning

**Impact :** Impossible de consommer l'API depuis une app mobile sans développement massif.

---

## PHASE 5 – SÉCURITÉ, LOGS, SAUVEGARDES ET DÉPLOIEMENT

### 5.1 Sécurité

**Secrets :**
- .env ignoré dans .gitignore ✅
- .env.example présent (sans valeurs sensibles) ✅
- Clés API en dur dans le code : À vérifier

**HTTPS :**
- Production : À vérifier
- Développement : HTTP (normal)

**Validation entrées :**
- Django forms : ✅
- Validation API : Partielle ❌
- Protection injections SQL : ✅ (ORM Django)
- Rate limiting : ❌ Absent

**Authentification :**
- Sessions Django ✅
- JWT : ❌ Absent
- App Check Firebase : ❌ Non activé (boutique)

### 5.2 Logs

**Fichiers de log :**
- logging configuré dans settings.py ✅
- Fichiers : À vérifier (logs/ ou stdout)

**Synchronisations :**
- Logs complets dans ecommerce/sync/services.py ✅
- Niveaux : INFO, ERROR ✅

**Imports :**
- Logs dans importer_commandes.py ✅

### 5.3 Sauvegardes

**Base locale :**
- Procédure de backup : À vérifier
- Export SQLite : Manuel (copie fichier)

**Firestore :**
- Export automatique : À configurer
- Rétention : À vérifier

### 5.4 Déploiement

**Backend :**
- Serveur : Inconnu (local probablement)
- URL : Non précisée
- Stabilité : Inconnue

**Frontend (Boutique) :**
- Firebase Hosting : ✅
- URL : À vérifier
- Déploiement automatique : À vérifier

**Synchronisation :**
- Fonctionne en continu : ❌ (pas de cron)
- Scripts disponibles : ✅

---

## PHASE 6 – SYNTHÈSE, LACUNES, POINTS DE BLOCAGE ET PRÉPARATION MOBILE

### 6.1 Tableau de synthèse

| Module | État | Manquant | Incohérent | Priorité |
|--------|------|----------|------------|----------|
| 1. Dashboard | Partiel | Cache, offline | - | 3 |
| 2. Facturation | Partiel | CMP/FIFO, lots, contre-écriture | Stock non mis à jour | **1 (CRITIQUE)** |
| 3. Caisse | Partiel | Hiérarchie, transferts, règle bloquante | Pas d'intégration Facturation | **1 (CRITIQUE)** |
| 4. Approvisionnements | Partiel | Services métier, répartition frais | Pas de mise à jour stock | **1 (CRITIQUE)** |
| 5. Articles | Fonctionnel | - | - | 2 |
| 6. Commandes | Fonctionnel | - | - | 2 |
| 7. Fournisseurs | Fonctionnel | Contacts multiples | - | 4 |
| 8. Clients | Fonctionnel | Gestion tiers | - | 4 |
| 9. Créanciers/Débiteurs | Fonctionnel | Échéances | - | 4 |
| 10. Patrimoine | Fonctionnel | - | - | 2 |
| 11. Rapports | Fonctionnel | Export PDF natif | - | 3 |
| 12. Paie | Fonctionnel | Congés, charges sociales | - | 3 |
| 13. Configurations | Fonctionnel | Interface RBAC | - | 3 |
| 14. PDF Generator | Fonctionnel | Bons de commande | - | 4 |
| 15. Conbuska AI | Partiel | /mem save, /mem recall | - | 5 |
| Activity Logs | Fonctionnel | - | - | 3 |
| API REST | Cassé | Auth JWT, pagination, docs | Endpoints incomplets | **1 (CRITIQUE)** |
| E-commerce Sync | Partiel | Cron, monitoring | Jamais testé prod | 2 |
| Import Commandes | Partiel | Cron, rollback | Jamais testé prod | 2 |
| Boutique PWA | Fonctionnel | Lighthouse preuves | - | 3 |

**Légende priorité :** 1 = Critique, 2 = Important, 3 = Moyen, 4 = Mineur, 5 = Cosmétique

### 6.2 Points bloquants pour intégration mobile

**❌ BLOQUANTS :**

1. **API REST incomplète** : Impossible de développer une app mobile sans API complète et stable
   - Manque : authentification JWT, pagination, filtres, documentation
   - Charge estimée : 3-4 semaines

2. **Modules moteurs cassés** : Facturation, Caisse, Approvisionnements ne fonctionnent pas correctement
   - Impact : données erronées si utilisées par mobile
   - Charge estimée : 4-6 semaines

3. **Pas d'authentification mobile** : Pas de JWT, pas de OAuth2
   - Charge estimée : 1 semaine

**⚠️ IMPORTANTS :**

4. **Synchronisation e-commerce non testée** : Risque de perte de données
   - Charge estimée : 2-3 semaines (tests + corrections)

5. **Pas de mode offline** : Problème pour utilisation mobile sur le terrain
   - Charge estimée : 2-3 semaines

6. **Pas de tests d'intégration** : Risque de régressions
   - Charge estimée : 2-3 semaines

### 6.3 Recommandations pour la suite

**Phase pré-mobile (OBLIGATOIRE) :**

1. **Corriger les 3 modules moteurs** (Facturation, Caisse, Approvisionnements)
   - Implémenter CMP/FIFO dans Facturation
   - Implémenter structure hiérarchique caisses + transferts
   - Implémenter services métier Approvisionnements
   - **Charge :** 4-6 semaines

2. **Compléter l'API REST**
   - Ajouter authentification JWT
   - Ajouter pagination sur tous les endpoints
   - Ajouter filtres et recherche
   - Générer documentation Swagger/OpenAPI
   - **Charge :** 3-4 semaines

3. **Tester la synchronisation e-commerce en production**
   - Configurer cron jobs
   - Tester bout en bout
   - Ajouter monitoring
   - **Charge :** 2-3 semaines

4. **Ajouter tests d'intégration**
   - Tests bout en bout des 3 modules moteurs
   - Tests API REST
   - **Charge :** 2-3 semaines

**Phase mobile (après pré-requis) :**

5. **Architecture API mobile**
   - Exposer API versionnée (/api/v1/)
   - Package partagé (si apps multiples)
   - **Charge :** 1 semaine

6. **Développement app Android gestion interne**
   - Dashboard mobile
   - Facturation mobile
   - Caisse mobile
   - Approvisionnements mobile
   - **Charge :** 12-16 semaines

7. **Développement app cliente**
   - Catalogue produits
   - Panier/commande
   - Suivi commande
   - **Charge :** 8-10 semaines

**Architecture cible recommandée :**

```
Backend (Django) → API REST v1 (JWT, pagination, filtres)
                    ↓
              Mobile App 1 (Flutter) – Gestion interne
                    ↓
              Mobile App 2 (Flutter) – Client
                    ↓
              Boutique PWA (Nuxt 4) – Client web
                    ↓
              Firebase (Firestore, Storage, Hosting)
```

**Technologies recommandées :**
- **Mobile** : Flutter (Dart) – une seule codebase pour Android + iOS
- **API** : Django REST Framework + SimpleJWT + drf-yasg (Swagger)
- **State management mobile** : Provider ou Riverpod
- **Tests** : pytest (backend), integration_tests (mobile)

---

## CONCLUSION

Le projet Conbuska est **globalement bien architecturé** mais **inachevé et non testé en production**. Les 3 modules moteurs (Facturation, Caisse, Approvisionnements) sont critiques et doivent être corrigés avant toute intégration mobile. L'API REST est insuffisante pour une consommation mobile.

**Recommandation :** Bloquer le développement mobile et concentrer les efforts sur la finalisation des modules core et la complétion de l'API REST (estimé 10-13 semaines de travail).

**Audit terminé. En attente de validation avant toute modification.**