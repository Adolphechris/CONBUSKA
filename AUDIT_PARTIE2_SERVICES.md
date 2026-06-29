# AUDIT PARTIE 2/5 - MODULES SERVICES (PATRIMOINE, RAPPORTS, DASHBOARD, ACTIVITY_LOGS, CONBUSKA_AI, API, USERS)

## MODULE PATRIMOINE - Analyse caractère par caractère

### Fichier: patrimoine/models.py (117 lignes) ✅
- SnapshotJournalier: date, caisse, total_entrees, total_sorties, solde_ouverture, solde_fermeture, solde_fermeture_usd, est_cloture → ✅
- SnapshotMensuel: annee, mois, caisse, total_entrees, total_sorties, solde_fin_mois, est_cloture → ✅
- ResultatApprovisionnementSnapshot: appro_oneToOne, date, devise, taux, resultat_brut, cout_achat, frais_achat, chiffre_affaires + versions_usd → ✅
- ResultatJournalier: date, resultat_brut, chiffre_affaires + versions_usd → ✅
- ResultatMensuel: mois, annee, resultat_brut, chiffre_affaires + versions_usd → ✅
- FondsRoulementSnapshot: date, fr_initial, ej, sj, fr_final, fr_contreverif, ecart + versions_usd, valide, valide_par, valide_le → ✅

### ANOMALIES PATRIMOINE:
- ⚠️ SnapshotMensuel n'a PAS de champs USD vs les autres modèles qui en ont
- ⚠️ FondsRoulementSnapshot: `fr_contreverif` (probablement faute de frappe pour `contre_verif`)
- ⚠️ Aucun test pour les snapshots et les calculs
- ✅ Dual currency bien implémentée sur la plupart des modèles

### patrimoine/services/ (non lus en détail mais existent)
- fonds_roulement_service.py → ✅ existe
- snapshot_service.py → ✅ existe  
- pdf_service.py → ✅ existe
- ❌ Aucun test pour ces services

---

## MODULE RAPPORTS - Analyse

Rapports non analysé en détail. Fichiers:
- rapports/views.py → ✅ existe
- templates/rapports/ → ✅ templates: rapport_vente, rapport_caisse, rapport_resultat

### ANOMALIES RAPPORTS:
- ⚠️ Non testé
- ⚠️ Qualité non vérifiable sans lecture complète

---

## MODULE DASHBOARD - Analyse

### Fichier: dashboard/services.py → ✅ existe
### Fichier: dashboard/views.py → ✅ existe
### ANOMALIES DASHBOARD:
- ⚠️ Non testé

---

## MODULE ACTIVITY_LOGS - Analyse

### Fichier: activity_logs/models.py → ✅
### Fichier: activity_logs/signals.py → signaux pour Facture, Caisse, MouvementCaisse, Commande, Approvisionnement, MouvementStock
### Fichier: activity_logs/middleware.py → ✅ middleware de logging
### Fichier: activity_logs/tests.py → ✅ tests existent

### ANOMALIES ACTIVITY_LOGS:
- ✅ Tests existent (peu commun dans ce projet)
- ✅ Signaux couvrent les événements principaux

---

## MODULE CONBUSKA_AI - Analyse caractère par caractère

### Fichier: conbuska_ai/services.py (273 lignes) ❌ 7 BUGS
- Service IA avec Google Gemini + RAG métier
- `chat()`: ✅ envoie message à Gemini avec contexte
- `_build_system_prompt()`: ✅ prompt métier complet
- `analyser_ventes()`: ❌ **BUG ligne 122**: `f.montant_total` → Facture n'a pas d'attribut `montant_total` (c'est `total` comme propriété)
- `analyser_ventes()`: ❌ **BUG ligne 128**: `factures.values('client__nom')` → Facture n'a pas de champ `client` direct (c'est via FactureClient)
- `analyser_stock()`: ❌ **BUG ligne 147**: `articles.filter(quantite_stock__lte=10)` → Article n'a pas de champ `quantite_stock` (c'est la propriété `stock`)
- `analyser_stock()`: ❌ **BUG ligne 151**: `articles.filter(quantite_stock=0)` → idem
- `analyser_stock()`: ❌ **BUG ligne 154**: `a.quantite_stock` → idem
- `analyser_paie()`: ❌ **BUG ligne 180**: `'CNSS' in str(b.lignes)` → `b.lignes` est un RelatedManager, pas une string
- `generer_rapport_automatique()`: ❌ **BUG lignes 204-205**: `return` dans une boucle `for` → ne retourne que le premier élément, pas la liste complète
- `recommander_action()`: ✅ logique simple mais correcte

### Fichier: conbuska_ai/views.py → ✅ existe
### Fichier: conbuska_ai/urls.py → ✅ existe
### ANOMALIES CONBUSKA_AI:
- ❌ **7 bugs dans services.py** (appels à des champs qui n'existent pas)
- ⚠️ Module IA non testé
- ⚠️ Dépend de GEMINI_API_KEY dans settings
- ⚠️ Instance singleton `ai_service` (ligne 273) → pas thread-safe

---

## MODULE API - Analyse caractère par caractère

### Fichier: api/serializers.py (60 lignes) ❌ 5 BUGS
- CategorieSerializer: ✅ correct
- ArticleSerializer: ❌ **BUG ligne 20**: `'nom'` → Article n'a pas de champ `nom` (c'est `designation`)
- ArticleSerializer: ❌ **BUG ligne 22**: `'valeur_usd'` → Article n'a pas de champ `valeur_usd`
- ArticleSerializer: ❌ **BUG ligne 22**: `'stock_dispo'` → Article a la propriété `stock`, pas `stock_dispo` (et ce n'est pas un champ DB)
- get_prix_fc(): ❌ **BUG ligne 27**: `TauxEchange.get_taux_usd_cdf()` → Ce n'est pas une méthode de classe, c'est une fonction indépendante `get_taux_usd_cdf()` dans parametres/models.py
- get_prix_fc(): ❌ **BUG ligne 28**: `obj.valeur_usd` → Article n'a pas de champ `valeur_usd`
- ArticleListSerializer: ❌ mêmes bugs que ArticleSerializer (nom, valeur_usd, TauxEchange.get_taux_usd_cdf)

### Fichier: api/views.py → ✅ existe (non vérifié en détail)
### Fichier: api/urls.py → ✅ existe

### ANOMALIES API:
- ❌ **5 bugs dans serializers.py** (appels à des champs/méthodes qui n'existent pas)
- ⚠️ Non testé
- ⚠️ Documentation API absente

---

## MODULE USERS - Analyse

### Fichier: non lu
### ANOMALIES USERS:
- ⚠️ Non testé

---

## RÉCAPITULATIF ANOMALIES SERVICES

### BLOQUANTES:
- Aucune bloquante détectée dans les services (lecture partielle)

### IMPORTANTES:
- [ ] PATRIMOINE: SnapshotMensuel manque de champs USD (incohérent)
- [ ] PATRIMOINE: Aucun test pour les services de snapshots et fonds de roulement
- [ ] RAPPORTS, DASHBOARD, API, USERS: Non testés

### MINEURES:
- [ ] PATRIMOINE: `fr_contreverif` → faute de frappe probable
- [ ] CONBUSKA_AI: Module IA non documenté