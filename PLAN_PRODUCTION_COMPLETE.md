# 🚀 PLAN DE PRODUCTION COMPLET — CONBUSCA → VERCEL + FIRESTORE + GITHUB CI

**Date de création** : 3 août 2026  
**Branche courante** : `release/v2.0` → migration vers `main`  
**Remote GitHub** : `https://github.com/Adolphechris/CONBUSKA.git`  
**Frontend** : Vercel (SSR statique Nuxt)  
**Backend** : VPS/serveur Linux (Django 5.2 + PostgreSQL + Redis)  
**Base de données temps réel** : Google Firestore (articles_publics, commandes_en_ligne)  
**Objectif** : 0 test échouant, déploiement production validé

---

## 📊 ÉTAT ACTUEL (3 août 2026)

### Tests pytest
| Métrique | Valeur |
|----------|--------|
| Tests collectés | 305 |
| Tests passants | 275 (90,2 %) |
| Tests échouants | **30** (9,8 %) |
| Tests cachés non collectés | 39 (5 fichiers `tests.py`) |
| **Total potentiel** | **344** |
| Modules sans tests | conbuska_ai, clients, fournisseurs, creanciers, parametres, users, users_management |

### Bugs critiques confirmés par inspection code + exécution tests
| # | Module | Fichier:Ligne | Bug | Tests impactés |
|---|--------|---------------|-----|----------------|
| 1 | paie | services.py:447 | `data.matricule` n'existe pas sur `AgentCreateInput` | 4 |
| 2 | paie | services.py:526 | `MouvementCaisseService` pas exporté depuis `caisse.services.__init__` (vide) | 7 |
| 3 | paie | services.py:497 | `AgentInactifError` non importé | 1 |
| 4 | paie | services.py:306 | `supprimer_bulletin` lève `ValueError` au lieu de `PaieDejaValideeError` | 1 |
| 5 | paie | services.py:158-264 | Prime d'ancienneté non conditionnelle, `total_primes` jamais 0 | 5 |
| 6 | ecommerce | import_commandes.py:334 | `Max` non importé (`from django.db.models import Max`) | 2 + 3 intégration |
| 7 | ecommerce | import_commandes.py:442,469 | `firestore` importé en bas du fichier (ligne 561) | integration |
| 8 | ecommerce | test_import_commandes.py:291 | `TransactionTestCase` casse l'isolation DB | 3 + 12 erreurs |
| 9 | factures | service delta CONFIRMED | Stock mal décrémenté/restitué | 5 |
| 10 | conbuska_ai | services.py:122-154,180,204 | 7 bugs champs/méthodes inexistants | 0 (pas de tests) |
| 11 | api | serializers.py:27-28,31,75 | `TauxEchange.get_taux_usd_cdf()` → fonction module | 0 (8 tests cachés) |
| 12 | api | serializers.py:17,62 | `stock_dispo` = IntegerField(default=0), ne lit pas `obj.stock` | 0 (8 tests cachés) |
| 13 | caisse | services/mouvement_caisse.py:57-70 | `_assert_solde_suffisant` ignore sorties existantes | potentiel |
| 14 | caisse | services/mouvement_caisse.py:100-104 | `_cleanup_transfert` supprime miroir sans rebuild | potentiel |

### Bugs mineurs / incohérences
| # | Module | Description |
|---|--------|-------------|
| M1 | caisse | `montant_usd` (MouvementCaisse) vs `valeur_usd` (tables liaison) → noms incohérents |
| M2 | commandes | `devise` est FK vers `parametres.Devise` (incohérent avec Facture/Appro CharField) |
| M3 | commandes | Pas de dual currency (valeur_usd, taux_creation) sur DetailsCommande |
| M4 | commandes | Pas de statut `ANNULEE` |
| M5 | patrimoine | `SnapshotMensuel` manque de champs USD |
| M6 | patrimoine | `fr_contreverif` probablement faute de frappe |
| M7 | paie | Prime ancienneté sans plafond (>20 ans = >100%) |
| M8 | paie | `calculer_bulletin` utilise `date.today()` au lieu de `agent.date_engagement` |
| M9 | paie | `try/except Exception pass` dans `valider_paie()` (avale les erreurs) |
| M10 | paie | `PaieValidationResult` manque `mouvement_caisse_cree` (attendu par tests) |
| M11 | clients/fournisseurs | `get_next_code` sans `transaction.atomic` (race condition) |
| M12 | produits | `code_barre` commenté (code mort) |
| M13 | produits | `stock` propriété fait requête DB à chaque appel (pas de cache) |
| M14 | pytest.ini | `python_files = test_*.py` exclut les fichiers `tests.py` |
| M15 | templates | `dual_amount` tag non chargé dans certains templates |

---

## 📋 PLAN PHASE PAR PHASE

### Phase 0 — Préparation infra (S24, Jour 1) — 3h

| # | Tâche | Commande / Fichier | Estim. | Dépendance |
|---|-------|---------------------|--------|------------|
| 0.1 | Créer branche `release/production-v1` | `git checkout -b release/production-v1 release/v2.0` | 10m | — |
| 0.2 | Corriger `pytest.ini` pour collecter `tests.py` | `python_files = test_*.py tests.py` | 5m | — |
| 0.3 | Créer `.github/workflows/ci.yml` | GitHub Actions | 1h | 0.1 |
| 0.4 | Créer endpoint `/health/` | `esm/urls.py` + vue | 30m | — |
| 0.5 | Créer `.env.production.example` | Template env prod | 15m | — |

**Critère de sortie** : Branche créée, CI passe sur master, health endpoint répond 200.

---

### Phase 1 — Correction bugs critiques (S24, Jours 2-3) — 6h

#### 1A. Paie — 4h

| # | Bug | Fichier:Ligne | Correction |
|---|-----|---------------|-----------|
| 1.1 | `matricule` manquant | paie/services.py:447 | Auto-générer matricule (`Max('matricule')+1` ou `1`) |
| 1.2 | `MouvementCaisseService` import | paie/services.py:526 | `from caisse.services.mouvement_caisse import MouvementCaisseService` |
| 1.3 | `AgentInactifError` non importé | paie/services.py:497 | Ajouter import dans `paie/exceptions.py` |
| 1.4 | `PaieDejaValideeError` non levé | paie/services.py:306 | Remplacer `ValueError` par `PaieDejaValideeError` |
| 1.5 | Prime ancienneté non conditionnelle | paie/services.py:158 | Rendre prime optionnelle ou fixer `date_engagement` dans factory |
| 1.6 | `try/except pass` | paie/services.py:559-561 | Logger l'erreur + propager `CaissePrincipaleFermeeError` |
| 1.7 | `PaieValidationResult` incomplet | paie/services.py:584 | Ajouter `mouvement_caisse_cree` et `mouvement_caisse_agent_cree` |
| 1.8 | `calculer_bulletin` utilise `date.today()` | paie/services.py:165 | Utiliser la date de paie (`mois`) |

#### 1B. Ecommerce — 1h

| # | Bug | Fichier:Ligne | Correction |
|---|-----|---------------|-----------|
| 1.9 | `Max` non importé | import_commandes.py:334 | `from django.db.models import Max` |
| 1.10 | Imports `firebase_admin` en bas | import_commandes.py:560-562 | Déplacer en haut du fichier |
| 1.11 | TransactionTestCase → TestCase | test_import_commandes.py:263 | Changer `TransactionTestCase` → `TestCase` |

#### 1C. Factures — 30m

| # | Bug | Fichier | Correction |
|---|-----|---------|-----------|
| 1.12 | Stock CONFIRMED mal géré | factures/services/facture_service.py | Vérifier logique delta + dispatch stock |

#### 1D. Conbuska AI — 30m

| # | Bug | Fichier:Ligne | Correction |
|---|-----|---------------|-----------|
| 1.13 | `f.montant_total` | services.py:122 | `f.total` (propriété) |
| 1.14 | `client__nom` inexistant | services.py:127-128 | Joindre via `FactureClient` |
| 1.15 | `quantite_stock` inexistant | services.py:148,151,154 | `stock` (propriété) → pas de filter DB |
| 1.16 | `str(b.lignes)` | services.py:180 | Itérer lignes, vérifier `libelle` |
| 1.17 | `return` dans boucle `for` | services.py:204-205 | Accumuler dans liste, `return` après |

#### 1E. API — 30m

| # | Bug | Fichier:Ligne | Correction |
|---|-----|---------------|-----------|
| 1.18 | `TauxEchange.get_taux_usd_cdf()` | serializers.py:31,75 | `from parametres.models import get_taux_usd_cdf` |
| 1.19 | `stock_dispo` fixé à 0 | serializers.py:17,62 | `SerializerMethodField` → `obj.stock` |

**Critère de sortie** : `pytest` → 0 test échouant, `pytest --no-header -q` → 0 failed.

---

### Phase 2 — Tests cachés & nouveaux tests (S24, Jour 4) — 4h

| # | Module | Action | Tests cibles |
|---|--------|--------|------------|
| 2.1 | caisse | Vérifier `tests.py` (15 tests) — redondant ou non ? | +15 tests potentiels |
| 2.2 | patrimoine | Vérifier `tests.py` (10 tests) | +10 tests |
| 2.3 | api | Vérifier `tests.py` (8 tests) — exécuter après fix 1.18-1.19 | +8 tests |
| 2.4 | dashboard | Vérifier `tests.py` (2 tests) | +2 tests |
| 2.5 | rapports | Vérifier `tests.py` (4 tests) | +4 tests |
| 2.8 | conbuska_ai | Créer `conbuska_ai/tests/test_services.py` | 5+ tests |
| 2.9 | clients/fournisseurs/creanciers | Créer tests modèles | 10+ tests |
| 2.10 | parametres | Créer tests `TauxEchange` | 5+ tests |
| 2.11 | ecommerce import | Corriger tests `TransactionTestCase` → mock Firestore + `Max` fix | 9 tests |

**Critère de sortie** : Tous les tests (y compris cachés) passent → 100 % vert.

---

### Phase 3 — CI/CD GitHub Actions (S24, Jour 4) — 1h

Fichier `.github/workflows/ci.yml` :

```yaml
# Jobs :
# 1. lint — ruff check, ruff format --check
# 2. typecheck — mypy (si configuré)
# 3. test — pytest avec --no-migrations
# 4. security — bandit (scan SAST)
# 5. build-vercel — vérifie que la boutique compile (npm run build)
# Seuil : 100 % tests passent, blocage merge si échec
```

**Critère de sortie** : CI passe sur chaque push. Badge GitHub Actions.

---

### Phase 4 — Configuration production (S24, Jour 5) — 2h

| # | Action | Fichier |
|---|--------|---------|
| 4.1 | Créer `.env.production` | Variables: DB, REDIS, FIREBASE, EMAIL, ALLOWED_HOSTS |
| 4.2 | Vérifier `esm/settings/prod.py` + `production.py` | DEBUG=False, HTTPS, HSTS, Redis cache |
| 4.3 | Configurer Gunicorn | `gunicorn-esm.service` systemd |
| 4.4 | Configurer Nginx | Reverse proxy + static + HTTPS |
| 4.5 | Configurer Redis | Cache + sessions + Celery broker |
| 4.6 | Configurer Celery | Worker + beat pour cron (sync Firestore + import) |
| 4.7 | Health checks | `/health/` endpoint → DB + Redis + Firebase |
| 4.8 | Sentry | Capture d'erreurs en production |

**Critère de sortie** : `python manage.py check --deploy` → 0 warnings.

---

### Phase 5 — Déploiement backend (S24, Jour 6) — 3h

| # | Action | Détails |
|---|--------|---------|
| 5.1 | Provisioning serveur | VPS Ubuntu 22.04, PostgreSQL 15, Redis 7 |
| 5.2 | Clone repo + venv | `git clone`, `python3 -m venv venv` |
| 5.3 | Install dépendances | `pip install -r requirements.txt` |
| 5.4 | Migrer base | `python manage.py migrate --settings=esm.settings.production` |
| 5.5 | Seed données | Taux de change, magasin principal, admin |
| 5.6 | Collecte statiques | `python manage.py collectstatic --noinput` |
| 5.7 | Démarrer services | `systemctl start gunicorn-esm celery-esm` |
| 5.8 | Configurer cron | `*/5 * * * * python manage.py sync_firestore` + `*/10 * * * * python manage.py importer_commandes` |

**Critère de sortie** : `/health/` → 200, Django admin accessible, API répond.

---

### Phase 6 — Déploiement frontend Vercel + Firestore (S24, Jour 6-7) — 4h

| # | Action | Détails |
|---|--------|---------|
| 6.1 | Configurer `vercel.json` | Output directory: `.output/public`, builds: `npm run build` |
| 6.2 | Connecter repo GitHub → Vercel | Import depuis `Adolphechris/CONBUSKA` |
| 6.3 | Variables d'environnement Vercel | `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_STORAGE_BUCKET`, etc. |
| 6.4 | Configurer Firestore Rules | `articles_publics`: read public, write admin; `commandes_en_ligne`: create public (App Check), read/write admin |
| 6.5 | Configurer Firebase Storage Rules | Read public images, write admin only |
| 6.6 | Domaine personnalisé | `boutique.conbuska.cd` → Vercel DNS |
| 6.7 | HTTPS | Vercel génère automatiquement (Let's Encrypt) |
| 6.8 | Test production | `https://boutique.conbuska.cd` → catalogue charge, panier fonctionne |

**Critère de sortie** : Boutique accessible sur domaine personnalisé, catalogue s'affiche, Firestore rules protégées.

---

### Phase 7 — Validation finale & monitoring (S24, Jour 7) — 2h

| # | Action | Détails |
|---|--------|---------|
| 7.1 | Tests de bout en bout | Publier article → sync Firestore → boutique affiche ✓ |
| 7.2 | Test import commande | Passer commande → Firestore → cron import → facture créée ✓ |
| 7.3 | Test paie complète | Créer agent → bulletin → valider → mouvement caisse ✓ |
| 7.4 | Sentry | Capture d'erreurs + alertes Slack/email |
| 7.5 | Prometheus + Grafana | Dashboard métriques (latence, erreurs 5xx, queue) |
| 7.6 | Sauvegarde automatique | `backup_v1.sh` → cron quotidien + test restore |
| 7.7 | Documentation | Mettre à jour `GUIDE_UTILISATEUR.md`, `GUIDE_TECHNIQUE.md` |
| 7.8 | Todo.md + tracker | Marquer 100 % des tâches complétées |

**Critère de sortie** : Tous les tests e2e passent, monitoring actif, documentation à jour.

---

## 📅 CALENDRIER (7 jours ouvrables)

```
S24 J1 (3h)  : [Phase 0] Infra + CI départ
S24 J2 (6h)  : [Phase 1A-B] Paie + Ecommerce fixes
S24 J3 (3h)  : [Phase 1C-E] Factures + AI + API fixes
S24 J4 (5h)  : [Phase 2-3] Tests cachés + CI complète
S24 J5 (2h)  : [Phase 4] Config production
S24 J6 (7h)  : [Phase 5-6] Deploy backend + Vercel
S24 J7 (2h)  : [Phase 7] Validation + monitoring
```

**Total estimé** : **28 heures** (~4 jours ouvrables temps plein)

---

## 🔗 WORKFLOW GIT

```
release/v2.0 (branche courante)
     │
     ├── git checkout -b release/production-v1
     │
     ├── Phase 1: git commit -m "fix: paie matricule + MouvementCaisseService import + Max import"
     ├── Phase 1: git commit -m "fix: conbuska_ai 7 bugs + api serializers 2 bugs"
     ├── Phase 2: git commit -m "fix: pytest.ini collecte tests.py + tests cache"
     ├── Phase 3: git commit -m "ci: github actions workflow"
     ├── Phase 4: git commit -m "config: .env.production.example + health endpoint"
     ├── Phase 5: git commit -m "docs: mise à jour todo.md + plan production"
     │
     ├── git push origin release/production-v1
     ├── → GitHub PR: release/production-v1 → main
     ├── → Vercel auto-deploy depuis main (frontend boutique/)
     └── → CI bloque merge si tests échouent
```

## 🎯 DEFINITION OF DONE (production)

| Critère | Vérification |
|---------|-------------|
| ✅ Tests | 0 test échouant (`pytest --tb=no -q` → 0 failed) |
| ✅ CI | GitHub Actions verte sur chaque push |
| ✅ Backend | `/health/` → 200, migrations appliquées, static collecté |
| ✅ Paie | Agent créé + bulletin calculé + validé + mouvement caisse |
| ✅ Ecommerce | Sync article → Firestore ✓ / Import commande → facture ✓ |
| ✅ API | Swagger à `/api/docs/`, JWT fonctionnel |
| ✅ Frontend | `https://boutique.conbuska.cd` → catalogue + panier + checkout |
| ✅ Firestore | Rules déployées, articles_publics synchronisés |
| ✅ Monitoring | Sentry + health check opérationnels |
| ✅ Sauvegarde | backup_v1.sh testé, restore testé |
| ✅ Documentation | todo.md mis à jour, GUIDE_UTILISATEUR.md à jour |
| ✅ Todo | 100% des tâches cochées |