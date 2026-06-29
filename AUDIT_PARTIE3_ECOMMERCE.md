# AUDIT PARTIE 3/5 - MODULE ECOMMERCE (BACKEND)

## Structure réelle vs ARCHITECTURE.md

### Ce que ARCHITECTURE.md décrit:
```
ecommerce/
├── sync/           # Sync sortante (Conbuska → Firestore)
├── import/         # Import commandes (Firestore → Conbuska) ← N'EXISTE PAS
└── tests/
```

### Ce qui existe RÉELLEMENT:
```
ecommerce/
├── __init__.py
├── admin.py         → Interface admin sync
├── apps.py
├── exceptions.py    → ✅ 7 exceptions métier
├── models.py        → ImageArticle, EcommerceLog
├── signals.py       → Signaux post_save Article/Stock
├── urls.py
├── views.py
├── management/commands/
│   ├── sync_firestore.py     → Commande sync
│   └── importer_commandes.py → Commande import
├── sync/
│   ├── __init__.py
│   ├── import_commandes.py   → Service import (À LA RACINE, pas dans import/)
│   ├── serializers.py        → Transformation Article → Firestore
│   ├── services.py           → FirestoreSyncService
│   ├── storage.py            → Upload images Firebase
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_firebase_connection.py
│   ├── test_import_commandes.py  → 16/23 tests échouent
│   └── test_serializers.py       → tests OK
```

### ANOMALIE STRUCTURELLE:
- ❌ **ARCHITECTURE.md** décrit un dossier `ecommerce/import/` qui **N'EXISTE PAS**
- ❌ Le fichier `import_commandes.py` est dans `sync/` au lieu de `import/`

---

## Analyse fichier par fichier

### ecommerce/exceptions.py ✅
- EcommerceException, FirebaseConnectionError, SyncError, ArticleNonPublieError, StockInsuffisantError, ArticleInexistantError, CommandeDejaImporteeError → 7 exceptions

### ecommerce/models.py ✅
- ImageArticle: article(FK), image_originale, image_webp_600, image_webp_150, est_principale, ordre, date_creation
- EcommerceLog: timestamp, evenement, article_code, commande_id, success, message, duree_ms → avec index

### ecommerce/signals.py ✅ (corrigé après lecture directe)
- Signaux post_save Article, pre_delete Article, post_save Stock
- Ils appellent FirestoreSyncService.sync_article(), sync_stock(), delete_article()
- **✅ Chaque signal a un try/except qui log l'erreur sans bloquer le save() (lignes 27-42, 50-59, 67-77)**
- **✅ Correction par rapport à mon analyse précédente: les signaux sont bien protégés**

### ecommerce/sync/services.py ⚠️
- FirestoreSyncService: sync_article(), sync_stock(), delete_article(), sync_all()
- **⚠️ Pas de tests unitaires pour ce service (hors test_firebase_connection)**

### ecommerce/sync/serializers.py ⚠️
- Serializers pour transformer Article → document Firestore
- **⚠️ Tests existent mais non vérifiés dans le détail**

### ecommerce/sync/storage.py ⚠️
- FirebaseStorageService: upload_and_transform(), delete_images()
- **⚠️ Non testé**

### ecommerce/sync/import_commandes.py ❌ BUGS
- **❌ BUG: imports firebase_admin en fin de fichier (lignes 560-562)** → NameError
- **❌ BUG: `_verifier_stocks()` utilise `article.stock` (ligne 285)** → cette propriété existe dans produits/models.py
- **❌ Le code est bien structuré mais les bugs d'import le rendent non fonctionnel**

### ecommerce/admin.py ✅
- Interface admin pour la synchronisation
- Template: templates/admin/ecommerce/sync_dashboard.html

### ecommerce/management/commands/
- sync_firestore.py → Commande CLI pour déclencher la sync
- importer_commandes.py → Commande CLI pour importer les commandes

### ecommerce/tests/test_import_commandes.py ❌
- **❌ 16/23 tests échouent** (classes TestVerificationArticles, TestVerificationStocks, TestCreationClient, TestImportStats → ✅ ; TestImportIntegration → ❌ car mock Firestore incorrect)

---

## RÉCAPITULATIF ANOMALIES ECOMMERCE

### BLOQUANTES:
- [ ] ecommerce/sync/import_commandes.py:560-562: import firestore en fin de fichier → NameError
- [ ] ARCHITECTURE.md décrit ecommerce/import/ qui n'existe pas
- [ ] ~~ecommerce/signals.py: pas de try/except~~ → **CORRIGÉ: les signaux sont bien protégés**

### IMPORTANTES:
- [ ] Tests d'intégration TestImportIntegration non fonctionnels (mock incorrect)
- [ ] storage.py non testé
- [ ] services.py non testé
- [ ] 16 tests ecommerce échouent

### MINEURES:
- [ ] import_commandes.py dans sync/ au lieu de import/
- [ ] Redondance: management/commands/importer_commandes.py ET sync/import_commandes.py