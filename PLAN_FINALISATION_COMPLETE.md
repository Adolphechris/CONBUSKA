# PLAN DE FINALISATION COMPLÈTE – CONBUSKA
## Canevas de travail avant intégration mobile

**Date :** 29 juin 2026  
**Version :** 1.0  
**Statut :** En attente de validation  
**Contrainte impérative :** Pas de calcul de coût de revient moyen. Chaque approvisionnement reste contrôlé au cas par cas.

---

## SOMMAIRE

1. [Principe fondamental](#principe-fondamental)
2. [Organisation du travail](#organisation-du-travail)
3. [Phase 1 – Modules Moteurs (4-6 semaines)](#phase-1--modules-moteurs)
4. [Phase 2 – API REST (3-4 semaines)](#phase-2--api-rest)
5. [Phase 3 – E-commerce (2-3 semaines)](#phase-3--e-commerce)
6. [Phase 4 – Tests et Qualité (2-3 semaines)](#phase-4--tests-et-qualité)
7. [Phase 5 – Finalisation (1 semaine)](#phase-5--finalisation)
8. [Checklist de validation](#checklist-de-validation)
9. [Estimation globale](#estimation-globale)

---

## PRINCIPE FONDAMENTAL

### ⚠️ RÈGLE ABSOLUE : PAS DE COÛT DE REVIENT MOYEN

**Ce qui est INTERDIT :**
- ❌ Calcul automatique d'un coût de revient moyen par article
- ❌ Moyenne des prix d'approvisionnements
- ❌ Méthode CUMP (Coût Unitaire Moyen Pondéré)
- ❌ Toute valorisation par moyenne

**Ce qui est OBLIGATOIRE :**
- ✅ Chaque approvisionnement est traité **individuellement**
- ✅ Les lots gardent leur **propre coût d'achat** (PAN, FA, PVD, PVG)
- ✅ La traçabilité est **totale** : on sait toujours quel lot vient de quel approvisionnement
- ✅ En cas de vente, on utilise le coût du **lot spécifique vendu**
- ✅ Si plusieurs lots existent pour un article, chacun a son propre coût

**Ce qui est AUTORISÉ :**
- ✅ Méthode FIFO automatisée (pour la gestion des péremptions)
- ✅ Valorisation automatique du stock (basée sur les coûts individuels des lots)

**Justification :**
- Précision comptable (chaque approvisionnement a ses propres frais)
- Traçabilité fiscale (obligation légale)
- Gestion des péremptions (FIFO naturel par dates, pas par coût)
- Flexibilité (négociations fournisseurs différentes par approvisionnement)

**Impact sur les modules :**
- **Articles** : stocker le coût par lot, pas par article
- **Facturation** : utiliser le coût du lot spécifique vendu (FIFO par date péremption)
- **Approvisionnements** : enregistrer PAN/FA/PVD/PVG par ligne
- **Patrimoine** : calculer les résultats par approvisionnement, pas par moyenne

---

## ORGANISATION DU TRAVAIL

### Structure des livrables

```
CONBUSKA/
├── PLAN_FINALISATION_COMPLETE.md          # Ce document
├── PHASE1_MODULES_MOTEURS/
│   ├── 1.1_FACTURATION/
│   │   ├── README.md                       # Spécifications détaillées
│   │   ├── checklist.md                    # Liste des tâches
│   │   └── tests/
│   │       ├── test_facturation_lots.py
│   │       └── test_contre_ecriture.py
│   ├── 1.2_CAISSE/
│   │   ├── README.md
│   │   ├── checklist.md
│   │   └── tests/
│   └── 1.3_APPROVISIONNEMENTS/
│       ├── README.md
│       ├── checklist.md
│       └── tests/
├── PHASE2_API_REST/
│   ├── README.md
│   ├── checklist.md
│   └── tests/
├── PHASE3_ECOMMERCE/
│   ├── README.md
│   ├── checklist.md
│   └── tests/
├── PHASE4_TESTS/
│   ├── README.md
│   ├── checklist.md
│   └── tests/
└── PHASE5_FINALISATION/
    ├── README.md
    └── checklist.md
```

### Méthodologie

**Pour chaque module :**
1. Lire le README.md du module
2. Cocher les tâches dans checklist.md au fur et à mesure
3. Écrire les tests AVANT le code (TDD)
4. Valider chaque fonctionnalité avant de passer à la suivante
5. Commit git après chaque tâche validée

**Règles de validation :**
- Tous les tests unitaires passent (vert)
- Tests d'intégration passent (vert)
- Manuel : scénario de test exécuté avec succès
- Code review (si équipe)
- Documentation à jour

---

## PHASE 1 – MODULES MOTEURS

**Durée estimée :** 4-6 semaines  
**Priorité :** CRITIQUE  
**Dépendances :** Aucune

### 1.1 MODULE FACTURATION

**Objectif :** Rendre le module complet et fonctionnel avec gestion des lots

**Fichiers à modifier/créer :**
- `factures/services/facture_service.py` (modifier)
- `factures/models.py` (vérifier)
- `factures/views.py` (modifier)
- `factures/forms.py` (modifier)
- `factures/urls.py` (compléter)
- `factures/tests.py` (compléter)
- `factures/tests/test_facturation_lots.py` (créer)
- `factures/tests/test_contre_ecriture.py` (créer)

**Tâches détaillées :**

#### Tâche 1.1.1 – Validation stock par lots
- [ ] Vérifier que chaque ligne de facture référence un lot spécifique
- [ ] Vérifier que la quantité demandée est disponible dans le lot
- [ ] Si plusieurs lots disponibles, proposer une sélection (FIFO par date péremption)
- [ ] Lever une erreur si stock insuffisant
- [ ] **Test :** `test_validation_stock_lots.py`

**Critère de validation :**
```python
# Exemple de comportement attendu
facture = Facture.objects.create(...)
facture.lignes.create(article=article, lot=lot_1, quantite=10)
# lot_1.quantite = 15 → OK
# lot_1.quantite = 5 → ERREUR "Stock insuffisant"
```

#### Tâche 1.1.2 – Calcul coût par lot (PAS DE MOYENNE)
- [ ] Récupérer le coût d'achat du lot spécifique (PAN + FA + PVD + PVG)
- [ ] Calculer le coût total de la ligne = coût_lot × quantite
- [ ] Calculer la marge = (PVD × quantite) - (coût_lot × quantite)
- [ ] Enregistrer le coût dans LigneFacture
- [ ] **Test :** `test_cout_par_lot.py`

**Critère de validation :**
```python
# Lot 1 : PAN=1000, FA=100, PVD=1500, PVG=2000
# Coût lot = 1000 + 100 = 1100
# Vente de 5 unités
# Coût vente = 1100 × 5 = 5500
# Pas de moyenne avec d'autres lots !
```

#### Tâche 1.1.3 – Mise à jour stock lors validation
- [ ] Décrémenter la quantité du lot vendu
- [ ] Créer un MouvementStock de type "sortie_vente"
- [ ] Mettre à jour le stock total de l'article
- [ ] Si lot épuisé, marquer comme "épuisé"
- [ ] **Test :** `test_mise_a_jour_stock_validation.py`

**Critère de validation :**
```python
# Avant validation
lot_1.quantite = 15
article.stock_total = 15

# Après validation facture (vente de 5)
lot_1.quantite = 10
article.stock_total = 10
mouvement = MouvementStock.objects.get(type="sortie_vente")
```

#### Tâche 1.1.4 – Génération écriture caisse automatique
- [ ] Lors validation facture, créer un MouvementCaisse
- [ ] Type : "vente" (entrée)
- [ ] Montant : total TTC de la facture
- [ ] Référence : numéro de facture
- [ ] Devise : USD ou FC selon facture
- [ ] **Test :** `test_generation_caisse_validation.py`

**Critère de validation :**
```python
# Facture validée
facture.valider()

# Vérifier écriture caisse
mouvement = MouvementCaisse.objects.get(reference=facture.numero)
assert mouvement.type == "vente"
assert mouvement.montant_usd == facture.total_usd
```

#### Tâche 1.1.5 – Mise à jour solde client
- [ ] Si client maison : incrémenter solde_client
- [ ] Si client comptoir : pas de solde (payé comptant)
- [ ] Enregistrer dans Client.solde_actuel
- [ ] **Test :** `test_mise_a_jour_solde_client.py`

#### Tâche 1.1.6 – Annulation contrôlée (contre-écriture)
- [ ] Créer FactureAnnulation liée à la facture originale
- [ ] Copier toutes les lignes avec quantités négatives
- [ ] Remettre en stock les lots (quantité +)
- [ ] Créer MouvementStock "entree_annulation"
- [ ] Créer MouvementCaisse "sortie_annulation" (remboursement)
- [ ] Décrementer solde client (si client maison)
- [ ] Marquer facture originale comme "annulée"
- [ ] **Test :** `test_contre_ecriture_complete.py`

**Critère de validation :**
```python
# Facture originale
facture = Facture.objects.get(numero="FAC-001")
facture.valider()
lot_1.quantite = 10

# Annulation
facture.annuler()

# Vérifications
lot_1.refresh_from_db()
assert lot_1.quantite == 15  # Stock restauré
assert facture.statut == "annulee"
assert MouvementCaisse.objects.filter(type="sortie_annulation").exists()
```

#### Tâche 1.1.7 – Gestion double devise
- [ ] Tous les montants stockés en USD et FC
- [ ] Taux de change récupéré depuis parametres
- [ ] Conversion automatique lors affichage
- [ ] **Test :** `test_double_devise.py`

#### Tâche 1.1.8 – Journalisation audit_log
- [ ] Logger création brouillon
- [ ] Logger validation
- [ ] Logger annulation
- [ ] Logger modifications lignes
- [ ] **Test :** `test_journalisation.py`

**Livrable Phase 1.1 :**
- Module Facturation 100% fonctionnel
- Tous les tests passent (couverture > 80%)
- Manuel de test exécuté avec succès
- Documentation API (si applicable)

---

### 1.2 MODULE CAISSE

**Objectif :** Rendre le module complet avec hiérarchie, transferts, règle bloquante

**Fichiers à modifier/créer :**
- `caisse/services/mouvement_caisse.py` (modifier)
- `caisse/models.py` (modifier)
- `caisse/views.py` (modifier)
- `caisse/forms.py` (modifier)
- `caisse/selectors.py` (compléter)
- `caisse/tests.py` (compléter)
- `caisse/tests/test_caisse_transferts.py` (créer)
- `caisse/tests/test_regle_bloquante.py` (créer)

**Tâches détaillées :**

#### Tâche 1.2.1 – Structure hiérarchique des caisses
- [ ] Modèle Caisse : ajouter champ `caisse_parent` (ForeignKey vers Caisse)
- [ ] Types de caisses :
  - Caisse principale (racine)
  - Caisse secondaire (enfant)
  - Caisse virtuelle (pour transferts)
- [ ] Vue arborescente des caisses
- [ ] **Test :** `test_structure_hierarchique.py`

**Critère de validation :**
```python
caisse_principale = Caisse.objects.create(nom="Caisse Centrale", type="principale")
caisse_magasin = Caisse.objects.create(nom="Caisse Magasin", type="secondaire", parent=caisse_principale)
caisse_virtuelle = Caisse.objects.create(nom="Transfert Interne", type="virtuelle")

# Arborescence
assert caisse_magasin.parent == caisse_principale
assert caisse_principale.enfants.count() == 1
```

#### Tâche 1.2.2 – Règle bloquante (solde insuffisant)
- [ ] Avant toute sortie, vérifier solde disponible
- [ ] Calculer solde = entrées - sorties
- [ ] Si sortie > solde : lever exception `SoldeInsuffisantException`
- [ ] Bloquer la transaction
- [ ] Logger la tentative
- [ ] **Test :** `test_regle_bloquante.py`

**Critère de validation :**
```python
caisse = Caisse.objects.create(nom="Caisse Test")
MouvementCaisse.objects.create(caisse=caisse, type="solde_initial", montant_usd=1000)

# Tentative de sortie de 1500 (solde = 1000)
with pytest.raises(SoldeInsuffisantException):
    MouvementCaisse.objects.create(caisse=caisse, type="sortie_charge", montant_usd=1500)
```

#### Tâche 1.2.3 – Transfert entre caisses
- [ ] Créer vue `TransfertEntreCaissesView`
- [ ] Créer formulaire `TransfertForm`
- [ ] Logique :
  1. Créer sortie dans caisse source (type "transfert_sortie")
  2. Créer entrée dans caisse destination (type "transfert_entree")
  3. Les deux mouvements liés par `transfert_id`
  4. Vérifier solde source avant sortie
- [ ] **Test :** `test_transfert_entre_caisses.py`

**Critère de validation :**
```python
caisse_a = Caisse.objects.create(nom="Caisse A")
caisse_b = Caisse.objects.create(nom="Caisse B")

# Solde initial caisse A = 1000
MouvementCaisse.objects.create(caisse=caisse_a, type="solde_initial", montant_usd=1000)

# Transfert de 500 vers caisse B
transfert = TransfertCaisses.effectuer(caisse_a, caisse_b, 500, "Transfert fonds")

# Vérifications
assert caisse_a.solde_actuel == 500
assert caisse_b.solde_actuel == 500
sortie = MouvementCaisse.objects.get(type="transfert_sortie", transfert=transfert)
entree = MouvementCaisse.objects.get(type="transfert_entree", transfert=transfert)
```

#### Tâche 1.2.4 – Tous les types d'entrées (7 types)
- [ ] Solde initial ✅ (déjà présent)
- [ ] Ventes (CA) ✅ (lié à facturation)
- [ ] Transfert reçu ✅ (lié à transferts)
- [ ] Paiements clients ✅ (à vérifier)
- [ ] Paiements créanciers ❌ (à implémenter)
- [ ] Paiements débiteurs ❌ (à implémenter)
- [ ] Autres entrées ❌ (à implémenter)

**Sous-catégories à créer :**
- Clients : paiement facture, acompte
- Créanciers : remboursement
- Débiteurs : recouvrement
- Autres : don, subvention, etc.

#### Tâche 1.2.5 – Toutes les catégories de sorties (6 catégories)
- [ ] Paiements créanciers ✅ (à vérifier)
- [ ] Paiements fournisseurs ✅ (à vérifier)
- [ ] Charges d'exploitation (avec sous-catégories) ⚠️ (à compléter)
  - Loyer
  - Électricité/eau
  - Téléphone/internet
  - Transport/logistique
  - Marketing/publicité
  - Entretien/maintenance
  - Fournitures bureau
  - Autres charges
- [ ] Charges personnelles (avec comptes bénéficiaires) ⚠️ (à compléter)
  - Salaires
  - Avances sur salaire
  - Prêts employés
  - Indemnités
- [ ] Paiements débiteurs ✅ (à vérifier)
- [ ] Transfert ✅ (lié à transferts)

#### Tâche 1.2.6 – Calcul automatique solde final
- [ ] Trigger automatique après chaque mouvement
- [ ] Solde = somme(entrées) - somme(sorties)
- [ ] Mettre à jour `Caisse.solde_actuel`
- [ ] Historique des soldes (pour graphiques)
- [ ] **Test :** `test_calcul_solde_automatique.py`

#### Tâche 1.2.7 – Intégration avec Facturation
- [ ] Lors validation facture → créer entrée caisse (type "vente")
- [ ] Lors paiement client → créer entrée caisse (type "paiement_client")
- [ ] Lors annulation facture → créer sortie caisse (type "annulation")
- [ ] **Test :** `test_integration_facturation_caisse.py`

#### Tâche 1.2.8 – Intégration avec Approvisionnements
- [ ] Lors paiement fournisseur → créer sortie caisse (type "paiement_fournisseur")
- [ ] Lors frais approvisionnement → créer sortie caisse (type "charge_achat")
- [ ] **Test :** `test_integration_approvisionnements_caisse.py`

#### Tâche 1.2.9 – Intégration avec Paie
- [ ] Lors paiement salaire → créer sortie caisse (type "salaire")
- [ ] **Test :** `test_integration_paie_caisse.py`

#### Tâche 1.2.10 – Journalisation et traçabilité
- [ ] Logger toutes les créations/modifications
- [ ] Capturer les modifications de solde
- [ ] **Test :** `test_journalisation_caisse.py`

**Livrable Phase 1.2 :**
- Module Caisse 100% fonctionnel
- Hiérarchie des caisses opérationnelle
- Transferts inter-caisses fonctionnels
- Règle bloquante active
- Tous les types d'entrées/sorties gérés
- Tous les tests passent (couverture > 80%)

---

### 1.3 MODULE APPROVISIONNEMENTS

**Objectif :** Rendre le module complet avec services métier, répartition frais, mise à jour stock

**Fichiers à modifier/créer :**
- `approvisionnements/services/` (créer tous les fichiers)
  - `approvisionnement_service.py`
  - `repartition_frais_service.py`
  - `mise_a_jour_stock_service.py`
- `approvisionnements/models.py` (vérifier)
- `approvisionnements/views.py` (modifier)
- `approvisionnements/forms.py` (modifier)
- `approvisionnements/urls.py` (compléter)
- `approvisionnements/tests.py` (compléter)
- `approvisionnements/tests/test_repartition_frais.py` (créer)
- `approvisionnements/tests/test_mise_a_jour_stock.py` (créer)

**Tâches détaillées :**

#### Tâche 1.3.1 – Service métier principal
- [ ] Créer `ApprovisionnementService`
- [ ] Méthode `creer_approvisionnement()` :
  1. Créer en-tête approvisionnement
  2. Créer lignes articles
  3. Créer section frais
  4. Lancer répartition frais
  5. Calculer totaux
  6. Sauvegarder
- [ ] Méthode `valider_approvisionnement()` :
  1. Vérifier que tous les lots sont créés
  2. Mettre à jour stocks
  3. Calculer coûts par lot (PAS DE MOYENNE)
  4. Mettre à jour dettes fournisseurs
  5. Générer écriture caisse (si paiement immédiat)
  6. Marquer comme "validé"
- [ ] Méthode `annuler_approvisionnement()` :
  1. Vérifier que pas encore validé
  2. Supprimer lots créés
  3. Annuler écritures
  4. Marquer comme "annulé"
- [ ] **Test :** `test_service_approvisionnement.py`

**Critère de validation :**
```python
service = ApprovisionnementService()

# Créer approvisionnement
appro = service.creer_approvisionnement(
    fournisseur=fournisseur,
    devise="USD",
    taux_change=2000,
    lignes=[
        {"article": article_1, "quantite": 100, "pan": 1000, "pvd": 1500},
        {"article": article_2, "quantite": 50, "pan": 500, "pvd": 800},
    ],
    frais={
        "transport": 10000,
        "douane": 5000,
        "assurance": 2000,
    }
)

# Valider
service.valider_approvisionnement(appro.id)

# Vérifications
assert appro.statut == "valide"
assert Lot.objects.filter(approvisionnement=appro).count() == 2
assert article_1.stock_total == 100
```

#### Tâche 1.3.2 – Répartition automatique des frais
- [ ] Créer `RepartitionFraisService`
- [ ] 7 services système obligatoires :
  1. Transport
  2. Douane
  3. Assurance
  4. Manutention
  5. Stockage
  6. Financiers (frais bancaires)
  7. Autres frais
- [ ] Méthodes de répartition :
  - Au prorata de la quantité
  - Au prorata du PAN (Prix d'Achat Net)
- [ ] Paramétrable dans parametres
- [ ] **Test :** `test_repartition_frais.py`

**Critère de validation :**
```python
# Approvisionnement
ligne_1: quantite=100, PAN=1000 → total PAN = 100 000
ligne_2: quantite=50, PAN=500 → total PAN = 25 000
total_PAN = 125 000

# Frais transport = 10 000
# Répartition au prorata PAN
frais_ligne_1 = 10 000 × (100 000 / 125 000) = 8 000
frais_ligne_2 = 10 000 × (25 000 / 125 000) = 2 000

# Coût final par lot
lot_1.cout_total = 100 000 + 8 000 = 108 000
lot_1.cout_unitaire = 108 000 / 100 = 1 080
```

#### Tâche 1.3.3 – Création des lots avec coûts
- [ ] Pour chaque ligne d'approvisionnement, créer un Lot
- [ ] Attribuer un numéro de lot unique (ex: LOT-2026-001)
- [ ] Enregistrer :
  - Quantité
  - Date péremption (si fournie)
  - PAN (Prix d'Achat Net)
  - FA (Frais d'Achat répartis)
  - PVD (Prix de Vente Garantie)
  - PVG (Prix de Vente Général)
  - Coût total = PAN + FA
  - Coût unitaire = Coût total / Quantité
- [ ] **Test :** `test_creation_lots.py`

**Critère de validation :**
```python
lot = Lot.objects.create(
    article=article_1,
    approvisionnement=appro,
    numero_lot="LOT-2026-001",
    quantite=100,
    date_peremption=date(2027, 6, 29),
    pan=100000,  # 1000 × 100
    fa=8000,  # frais répartis
    pvd=150000,  # 1500 × 100
    pvg=200000,  # 2000 × 100
    cout_total=108000,
    cout_unitaire=1080
)
```

#### Tâche 1.3.4 – Mise à jour des stocks
- [ ] Créer `MiseAJourStockService`
- [ ] Lors validation approvisionnement :
  1. Créer un Lot pour chaque ligne
  2. Incrémenter `Article.stock_total`
  3. Créer `MouvementStock` de type "entree_approvisionnement"
  4. Lier le mouvement au lot
- [ ] **Test :** `test_mise_a_jour_stock_appro.py`

**Critère de validation :**
```python
# Avant approvisionnement
article.stock_total = 500

# Après validation appro (100 unités)
article.refresh_from_db()
assert article.stock_total == 600

mouvement = MouvementStock.objects.get(type="entree_approvisionnement")
assert mouvement.quantite == 100
assert mouvement.lot == lot_1
```

#### Tâche 1.3.5 – Mise à jour des dettes fournisseurs
- [ ] Calculer dette = total approvisionnement
- [ ] Créer ou mettre à jour `Fournisseur.solde_actuel`
- [ ] Créer historique des dettes
- [ ] **Test :** `test_mise_a_jour_dettes.py`

#### Tâche 1.3.6 – Paiement immédiat optionnel
- [ ] Champ `paiement_immediat` dans Approvisionnement
- [ ] Si True :
  1. Créer MouvementCaisse de type "paiement_fournisseur"
  2. Sortie du montant total
  3. Marquer dette comme "payée"
- [ ] Si False :
  1. Créer DetteFournisseur
  2. Marquer comme "en attente"
- [ ] **Test :** `test_paiement_immediat.py`

#### Tâche 1.3.7 – Intégration avec Caisse
- [ ] Si paiement immédiat → créer sortie caisse
- [ ] Si paiement différé → créer échéance
- [ ] **Test :** `test_integration_caisse.py`

#### Tâche 1.3.8 – Journalisation
- [ ] Logger création
- [ ] Logger validation
- [ ] Logger annulation
- [ ] **Test :** `test_journalisation_appro.py`

**Livrable Phase 1.3 :**
- Module Approvisionnements 100% fonctionnel
- Services métier complets
- Répartition frais opérationnelle
- Lots créés avec coûts individuels (pas de moyenne)
- Stocks mis à jour automatiquement
- Dettes fournisseurs gérées
- Tous les tests passent (couverture > 80%)

---

## PHASE 2 – API REST

**Durée estimée :** 3-4 semaines  
**Priorité :** CRITIQUE  
**Dépendances :** Phase 1 (modules moteurs)

**Objectif :** API REST complète, sécurisée, documentée pour consommation mobile

**Fichiers à modifier/créer :**
- `api/serializers.py` (compléter)
- `api/views.py` (compléter)
- `api/urls.py` (compléter)
- `api/permissions.py` (créer)
- `api/pagination.py` (créer)
- `api/filters.py` (créer)
- `api/throttling.py` (créer)
- `api/tests/` (créer)
- `esm/settings/base.py` (modifier pour ajouter DRF config)

**Tâches détaillées :**

#### Tâche 2.1 – Authentification JWT
- [ ] Installer `djangorestframework-simplejwt`
- [ ] Configurer dans settings.py
- [ ] Créer endpoints :
  - POST /api/auth/token/ (obtenir token)
  - POST /api/auth/token/refresh/ (rafraîchir)
  - POST /api/auth/token/verify/ (vérifier)
- [ ] Créer vue `LoginView` et `LogoutView`
- [ ] **Test :** `test_auth_jwt.py`

**Critère de validation :**
```bash
# Obtenir token
POST /api/auth/token/
{
  "username": "admin",
  "password": "password"
}

# Réponse
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

# Utiliser token
GET /api/articles/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Tâche 2.2 – Pagination
- [ ] Créer `PaginationPersonnalisee` (page_size=20, max_page_size=100)
- [ ] Appliquer sur tous les ViewSets
- [ ] Support query params : `?page=2&page_size=50`
- [ ] **Test :** `test_pagination.py`

**Critère de validation :**
```bash
GET /api/articles/?page=2&page_size=20

# Réponse
{
  "count": 150,
  "next": "http://api.conbuska.com/api/articles/?page=3&page_size=20",
  "previous": "http://api.conbuska.com/api/articles/?page=1&page_size=20",
  "results": [...]
}
```

#### Tâche 2.3 – Filtres et recherche
- [ ] Installer `django-filter`
- [ ] Créer filtres pour chaque modèle :
  - Articles : nom, catégorie, stock_min, stock_max, publie_en_ligne
  - Clients : nom, telephone, solde_min, solde_max
  - Fournisseurs : nom, type
  - Factures : date_debut, date_fin, statut, client
  - MouvementsCaisse : date_debut, date_fin, type, caisse
  - Approvisionnements : date_debut, date_fin, fournisseur, statut
- [ ] Recherche full-text sur : nom, référence
- [ ] **Test :** `test_filtres.py`

**Critère de validation :**
```bash
GET /api/articles/?categorie=3&stock_min=10&search=farine

# Retourne articles catégorie 3, stock >= 10, contenant "farine"
```

#### Tâche 2.4 – Endpoints Articles
- [ ] GET /api/articles/ (liste paginée)
- [ ] POST /api/articles/ (création)
- [ ] GET /api/articles/{id}/ (détail)
- [ ] PUT /api/articles/{id}/ (modification)
- [ ] PATCH /api/articles/{id}/ (modification partielle)
- [ ] DELETE /api/articles/{id}/ (suppression)
- [ ] GET /api/articles/{id}/lots/ (lots de l'article)
- [ ] GET /api/articles/{id}/stock/ (stock détaillé)
- [ ] GET /api/categories/ (liste catégories)
- [ ] **Test :** `test_endpoints_articles.py`

#### Tâche 2.5 – Endpoints Clients
- [ ] GET /api/clients/
- [ ] POST /api/clients/
- [ ] GET /api/clients/{id}/
- [ ] PUT /api/clients/{id}/
- [ ] DELETE /api/clients/{id}/
- [ ] GET /api/clients/{id}/factures/ (historique)
- [ ] GET /api/clients/{id}/solde/ (solde actuel)
- [ ] **Test :** `test_endpoints_clients.py`

#### Tâche 2.6 – Endpoints Fournisseurs
- [ ] GET /api/fournisseurs/
- [ ] POST /api/fournisseurs/
- [ ] GET /api/fournisseurs/{id}/
- [ ] PUT /api/fournisseurs/{id}/
- [ ] DELETE /api/fournisseurs/{id}/
- [ ] GET /api/fournisseurs/{id}/dettes/ (dettes)
- [ ] GET /api/fournisseurs/{id}/approvisionnements/ (historique)
- [ ] **Test :** `test_endpoints_fournisseurs.py`

#### Tâche 2.7 – Endpoints Factures
- [ ] GET /api/factures/
- [ ] POST /api/factures/ (créer brouillon)
- [ ] GET /api/factures/{id}/
- [ ] PUT /api/factures/{id}/
- [ ] DELETE /api/factures/{id}/
- [ ] POST /api/factures/{id}/valider/ (valider)
- [ ] POST /api/factures/{id}/annuler/ (annuler)
- [ ] GET /api/factures/{id}/lignes/ (lignes)
- [ ] POST /api/factures/{id}/lignes/ (ajouter ligne)
- [ ] DELETE /api/factures/{id}/lignes/{ligne_id}/ (supprimer ligne)
- [ ] GET /api/factures/{id}/pdf/ (générer PDF)
- [ ] **Test :** `test_endpoints_factures.py`

#### Tâche 2.8 – Endpoints Caisse
- [ ] GET /api/caisses/
- [ ] GET /api/caisses/{id}/
- [ ] GET /api/caisses/{id}/mouvements/ (mouvements)
- [ ] GET /api/caisses/{id}/solde/ (solde actuel)
- [ ] POST /api/caisses/{id}/entree/ (créer entrée)
- [ ] POST /api/caisses/{id}/sortie/ (créer sortie)
- [ ] POST /api/transferts/ (créer transfert)
- [ ] GET /api/transferts/{id}/ (détail transfert)
- [ ] **Test :** `test_endpoints_caisse.py`

#### Tâche 2.9 – Endpoints Approvisionnements
- [ ] GET /api/approvisionnements/
- [ ] POST /api/approvisionnements/ (créer brouillon)
- [ ] GET /api/approvisionnements/{id}/
- [ ] PUT /api/approvisionnements/{id}/
- [ ] DELETE /api/approvisionnements/{id}/
- [ ] POST /api/approvisionnements/{id}/valider/ (valider)
- [ ] POST /api/approvisionnements/{id}/annuler/ (annuler)
- [ ] GET /api/approvisionnements/{id}/lignes/ (lignes)
- [ ] GET /api/approvisionnements/{id}/lots/ (lots créés)
- [ ] **Test :** `test_endpoints_approvisionnements.py`

#### Tâche 2.10 – Endpoints Articles (complément)
- [ ] GET /api/articles/{id}/mouvements/ (historique mouvements)
- [ ] GET /api/articles/{id}/alertes/ (alertes stock/péremption)
- [ ] GET /api/lots/ (liste lots)
- [ ] GET /api/lots/{id}/ (détail lot)
- [ ] **Test :** `test_endpoints_articles_complement.py`

#### Tâche 2.11 – Endpoints Rapports
- [ ] GET /api/rapports/ventes/?date_debut=X&date_fin=Y
- [ ] GET /api/rapports/caisses/?date_debut=X&date_fin=Y
- [ ] GET /api/rapports/resultats/?periode=Mois/Année
- [ ] GET /api/rapports/articles/rotation/
- [ ] **Test :** `test_endpoints_rapports.py`

#### Tâche 2.12 – Endpoints Patrimoine
- [ ] GET /api/patrimoine/journal/
- [ ] GET /api/patrimoine/resultats/
- [ ] GET /api/patrimoine/fr/ (fonds roulement)
- [ ] GET /api/patrimoine/fr/historique/
- [ ] **Test :** `test_endpoints_patrimoine.py`

#### Tâche 2.13 – Permissions et RBAC
- [ ] Créer `IsAdmin` (admin seulement)
- [ ] Créer `IsGerant` (gérant + admin)
- [ ] Créer `IsCaissier` (caissier + gérant + admin)
- [ ] Créer `IsMagasinier` (magasinier + gérant + admin)
- [ ] Appliquer permissions sur chaque endpoint
- [ ] **Test :** `test_permissions.py`

**Critère de validation :**
```python
# Caissier peut créer entrée caisse
response = client.post('/api/caisses/1/entree/', data, HTTP_AUTHORIZATION='Bearer ...')
assert response.status_code == 201

# Caissier NE PEUT PAS créer approvisionnement
response = client.post('/api/approvisionnements/', data, HTTP_AUTHORIZATION='Bearer ...')
assert response.status_code == 403
```

#### Tâche 2.14 – Rate limiting
- [ ] Configurer throttling :
  - Authenticated : 1000 requêtes/heure
  - Anonyme : 100 requêtes/heure
- [ ] **Test :** `test_rate_limiting.py`

#### Tâche 2.15 – Documentation Swagger/OpenAPI
- [ ] Installer `drf-yasg`
- [ ] Générer schéma OpenAPI
- [ ] Créer endpoint /api/docs/ (Swagger UI)
- [ ] Créer endpoint /api/redoc/ (ReDoc)
- [ ] Documenter chaque endpoint (description, paramètres, réponses)
- [ ] **Test :** Vérifier que docs sont accessibles

**Critère de validation :**
```bash
# Accéder à la documentation
GET /api/docs/

# Vérifier que tous les endpoints sont documentés
# Vérifier que les exemples sont corrects
```

#### Tâche 2.16 – Versioning API
- [ ] Structurer URLs : /api/v1/
- [ ] Préparer pour futures versions
- [ ] **Test :** `test_versioning.py`

**Livrable Phase 2 :**
- API REST complète (tous endpoints)
- Authentification JWT fonctionnelle
- Pagination, filtres, recherche
- Permissions RBAC appliquées
- Rate limiting actif
- Documentation Swagger générée
- Tous les tests passent (couverture > 80%)

---

## PHASE 3 – E-COMMERCE

**Durée estimée :** 2-3 semaines  
**Priorité :** IMPORTANT  
**Dépendances :** Phase 1, Phase 2

**Objectif :** Finaliser et tester la synchronisation e-commerce en production

**Tâches détaillées :**

#### Tâche 3.1 – Configuration cron jobs
- [ ] Configurer cron sur serveur (Linux) ou tâche planifiée (Windows)
- [ ] Synchronisation sortante : toutes les 5 minutes
  ```bash
  */5 * * * * cd /path/to/conbuska && python manage.py sync_firestore
  ```
- [ ] Import commandes : toutes les 10 minutes
  ```bash
  */10 * * * * cd /path/to/conbuska && python manage.py importer_commandes
  ```
- [ ] Nettoyage logs : tous les jours à 2h
  ```bash
  0 2 * * * cd /path/to/conbuska && python manage.py cleanup_logs
  ```
- [ ] **Test :** Vérifier que cron s'exécute

#### Tâche 3.2 – Monitoring et alertes
- [ ] Créer tableau de bord monitoring (admin)
- [ ] Indicateurs :
  - Dernière sync (timestamp)
  - Nombre articles synchronisés
  - Nombre erreurs (dernières 24h)
  - Nombre commandes importées
  - Statut Firebase (connecté/déconnecté)
- [ ] Alertes email si :
  - > 5 erreurs consécutives
  - Firebase déconnecté
  - Échec sync > 30 min
- [ ] **Test :** Simuler erreurs et vérifier alertes

#### Tâche 3.3 – Tests bout en bout synchronisation
- [ ] Test 1 : Créer article dans Conbuska → Vérifier Firestore
- [ ] Test 2 : Modifier article → Vérifier mise à jour Firestore
- [ ] Test 3 : Dépublier article → Vérifier suppression Firestore
- [ ] Test 4 : Upload image → Vérifier Storage
- [ ] Test 5 : Créer commande dans boutique → Vérifier Firestore
- [ ] Test 6 : Importer commande → Vérifier Conbuska
- [ ] Test 7 : Vérifier mise à jour stock après import
- [ ] **Documenter chaque scénario**

#### Tâche 3.4 – Gestion des erreurs
- [ ] Rollback en cas d'erreur partielle
- [ ] Réessai automatique (3 tentatives)
- [ ] Logging détaillé
- [ ] Notification admin en cas d'échec
- [ ] **Test :** Simuler pannes Firebase

#### Tâche 3.5 – Validation boutique PWA
- [ ] Tester toutes les pages (15 pages)
- [ ] Tester panier (ajout, suppression, modification)
- [ ] Tester checkout (formulaire, validation)
- [ ] Tester confirmation commande
- [ ] Tester recherche
- [ ] Tester responsive (mobile, tablet, desktop)
- [ ] **Test :** Lighthouse (objectif ≥ 90)

#### Tâche 3.6 – Déploiement boutique
- [ ] Vérifier configuration Firebase Hosting
- [ ] Déployer en production
- [ ] Vérifier HTTPS
- [ ] Vérifier domaine personnalisé (si applicable)
- [ ] Tester en production
- [ ] **Livrable :** URL publique accessible

#### Tâche 3.7 – Tests Firestore/Storage
- [ ] Vérifier règles Firestore (sécurité)
- [ ] Vérifier règles Storage (sécurité)
- [ ] Tester lecture/écriture depuis boutique
- [ ] Tester upload images
- [ ] Vérifier redimensionnement automatique
- [ ] **Test :** Tenter accès non autorisé (doit échouer)

**Livrable Phase 3 :**
- Cron jobs configurés et fonctionnels
- Monitoring opérationnel
- Tests bout en bout réussis
- Boutique déployée en production
- Synchronisation validée en production
- Documentation exploitation

---

## PHASE 4 – TESTS ET QUALITÉ

**Durée estimée :** 2-3 semaines  
**Priorité :** IMPORTANT  
**Dépendances :** Phase 1, Phase 2, Phase 3

**Objectif :** Atteindre une couverture de tests > 80% et valider la qualité globale

**Tâches détaillées :**

#### Tâche 4.1 – Tests unitaires manquants
- [ ] Dashboard : tests/widgets (couverture actuelle : ~30%)
- [ ] Facturation : tests/complets (couverture actuelle : ~40%)
- [ ] Caisse : tests/complets (couverture actuelle : ~50%)
- [ ] Approvisionnements : tests/complets (couverture actuelle : ~10%)
- [ ] Clients : tests/complets (couverture actuelle : ~60%)
- [ ] Fournisseurs : tests/complets (couverture actuelle : ~60%)
- [ ] Créanciers/Débiteurs : tests/complets (couverture actuelle : ~60%)
- [ ] Paie : tests/complets (couverture actuelle : ~50%)
- [ ] Patrimoine : tests/complets (couverture actuelle : ~40%)
- [ ] Rapports : tests/complets (couverture actuelle : ~30%)
- [ ] Conbuska AI : tests/complets (couverture actuelle : 0%)
- [ ] **Objectif :** Couverture > 80% pour chaque module

#### Tâche 4.2 – Tests d'intégration
- [ ] Scénario 1 : Vente complète (Facturation → Caisse → Stock → Client)
- [ ] Scénario 2 : Approvisionnement complet (Commande → Appro → Stock → Dette)
- [ ] Scénario 3 : Paiement salaire (Paie → Caisse)
- [ ] Scénario 4 : Transfert caisse (Caisse A → Caisse B)
- [ ] Scénario 5 : Annulation facture (contre-écriture complète)
- [ ] Scénario 6 : Génération rapport (ventes + caisses + résultats)
- [ ] **Chaque scénario :** données de test → exécution → vérifications

#### Tâche 4.3 – Tests API REST
- [ ] Tester tous les endpoints (200, 201, 400, 401, 403, 404)
- [ ] Tester authentification JWT
- [ ] Tester pagination
- [ ] Tester filtres
- [ ] Tester permissions RBAC
- [ ] Tester rate limiting
- [ ] **Objectif :** 100% des endpoints testés

#### Tâche 4.4 – Tests e-commerce
- [ ] Sync sortante : 10 articles → Firestore
- [ ] Sync sortante : modification article → Firestore
- [ ] Sync sortante : suppression article → Firestore
- [ ] Import commande : créer commande boutique → importer → vérifier Conbuska
- [ ] Import commande : stock insuffisant → vérifier gestion erreur
- [ ] **Objectif :** 100% des scénarios testés

#### Tâche 4.5 – Tests de performance
- [ ] Dashboard : temps de chargement < 2s
- [ ] API : temps de réponse < 500ms (p95)
- [ ] Facturation : validation < 1s
- [ ] Caisse : mouvement < 200ms
- [ ] Approvisionnement : validation < 2s
- [ ] **Outil :** Django Debug Toolbar, pytest-benchmark

#### Tâche 4.6 – Tests de sécurité
- [ ] Injection SQL : vérifier protection ORM
- [ ] XSS : vérifier échappement templates
- [ ] CSRF : vérifier tokens
- [ ] Authentification : tester accès non autorisé
- [ ] Permissions : tester élévation de privilèges
- [ ] **Outil :** OWASP ZAP, Bandit

#### Tâche 4.7 – Tests de charge
- [ ] 100 utilisateurs simultanés (dashboard)
- [ ] 50 requêtes API simultanées
- [ ] 10 transactions caisse simultanées
- [ ] **Outil :** Locust, JMeter

#### Tâche 4.8 – Correction des bugs
- [ ] Prioriser par sévérité (critique, majeur, mineur)
- [ ] Corriger tous les bugs critiques
- [ ] Corriger tous les bugs majeurs
- [ ] Documenter bugs mineurs (pour futur)
- [ ] **Outil :** GitHub Issues, Jira

**Livrable Phase 4 :**
- Couverture tests > 80%
- Tous les tests passent (vert)
- Tests d'intégration validés
- Tests de performance acceptables
- Tests de sécurité validés
- Bugs critiques et majeurs corrigés

---

## PHASE 5 – FINALISATION

**Durée estimée :** 1 semaine  
**Priorité :** CRITIQUE  
**Dépendances :** Phase 1, 2, 3, 4

**Objectif :** Préparer le projet pour la phase mobile

**Tâches détaillées :**

#### Tâche 5.1 – Documentation
- [ ] **README.md** : mettre à jour avec instructions installation
- [ ] **ARCHITECTURE.md** : compléter avec schémas à jour
- [ ] **API.md** : documentation complète des endpoints
- [ ] **DEPLOIEMENT.md** : guide de déploiement production
- [ ] **UTILISATION.md** : manuel utilisateur
- [ ] **CONTRIBUTING.md** : guide pour contributeurs
- [ ] **CHANGELOG.md** : historique des versions

#### Tâche 5.2 – Scripts utilitaires
- [ ] `scripts/backup_db.sh` : sauvegarde base de données
- [ ] `scripts/restore_db.sh` : restauration
- [ ] `scripts/deploy.sh` : déploiement automatisé
- [ ] `scripts/seed_data.py` : données de test
- [ ] `scripts/health_check.py` : vérification santé système

#### Tâche 5.3 – Configuration production
- [ ] **settings/production.py** : créer
  - DEBUG = False
  - ALLOWED_HOSTS = ['domaine.com']
  - DATABASES = PostgreSQL
  - CELERY_BROKER_URL = Redis
  - CACHE_BACKEND = Redis
  - LOGGING = fichiers rotatifs
  - SECURE_SSL_REDIRECT = True
  - SESSION_COOKIE_SECURE = True
  - CSRF_COOKIE_SECURE = True
- [ ] **Variables d'environnement** : documenter toutes les variables
- [ ] **.env.production** : template (ne pas commit)

#### Tâche 5.4 – Sauvegardes
- [ ] Configurer backup automatique base de données (quotidien)
- [ ] Configurer export Firestore (hebdomadaire)
- [ ] Tester restauration
- [ ] Documenter procédure

#### Tâche 5.5 – Monitoring production
- [ ] Installer Sentry (erreurs)
- [ ] Installer Prometheus + Grafana (métriques)
- [ ] Configurer alertes :
  - Erreur 500
  - Temps réponse > 2s
  - Base de données inaccessible
  - Firebase déconnecté
- [ ] Dashboard monitoring

#### Tâche 5.6 – Formation équipe
- [ ] Session formation : architecture du projet
- [ ] Session formation : modules métier
- [ ] Session formation : déploiement
- [ ] Session formation : monitoring
- [ ] Documentation interne

#### Tâche 5.7 – Validation finale
- [ ] Checklist de validation (voir section suivante)
- [ ] Revue de code complète
- [ ] Validation par le métier (Ets La Lumière)
- [ ] Signature du rapport d'audit final

**Livrable Phase 5 :**
- Documentation complète
- Scripts utilitaires opérationnels
- Configuration production prête
- Sauvegardes configurées
- Monitoring actif
- Équipe formée
- Validation finale signée

---

## CHECKLIST DE VALIDATION

### Modules Moteurs

**Facturation :**
- [ ] Création facture brouillon fonctionne
- [ ] Ajout/suppression lignes fonctionne
- [ ] Validation facture :
  - [ ] Vérifie stock par lots
  - [ ] Décrémente lots
  - [ ] Crée écriture caisse
  - [ ] Met à jour solde client
  - [ ] Journalise
- [ ] Annulation facture :
  - [ ] Contre-écriture complète
  - [ ] Restaure stocks
  - [ ] Crée remboursement caisse
  - [ ] Met à jour solde client
- [ ] Gestion double devise (USD/FC)
- [ ] Impression PDF fonctionne
- [ ] Tous les tests passent

**Caisse :**
- [ ] Hiérarchie caisses opérationnelle
- [ ] CRUD mouvements fonctionne
- [ ] Règle bloquante active (solde insuffisant rejeté)
- [ ] Transfert entre caisses :
  - [ ] Crée 2 écritures (sortie + entrée)
  - [ ] Liées par transfert_id
  - [ ] Vérifie solde avant sortie
- [ ] Tous les types d'entrées (7) fonctionnent
- [ ] Toutes les catégories de sorties (6) fonctionnent
- [ ] Calcul solde automatique
- [ ] Intégration Facturation OK
- [ ] Intégration Approvisionnements OK
- [ ] Intégration Paie OK
- [ ] Tous les tests passent

**Approvisionnements :**
- [ ] Création approvisionnement fonctionne
- [ ] Répartition frais (7 services) fonctionne
- [ ] Validation approvisionnement :
  - [ ] Crée lots avec coûts individuels
  - [ ] Met à jour stocks
  - [ ] Met à jour dettes fournisseurs
  - [ ] Génère écriture caisse (si paiement immédiat)
- [ ] Annulation approvisionnement fonctionne
- [ ] Pas de calcul de coût moyen (vérifié)
- [ ] Tous les tests passent

### API REST

- [ ] Authentification JWT fonctionne
- [ ] Pagination fonctionne sur tous les endpoints
- [ ] Filtres fonctionnent
- [ ] Recherche fonctionne
- [ ] Permissions RBAC appliquées
- [ ] Rate limiting actif
- [ ] Documentation Swagger accessible
- [ ] Tous les endpoints testés
- [ ] Tous les tests passent

### E-commerce

- [ ] Cron jobs configurés
- [ ] Sync sortante testée en production
- [ ] Import commandes testé en production
- [ ] Monitoring opérationnel
- [ ] Alertes configurées
- [ ] Boutique déployée et accessible
- [ ] Tests bout en bout réussis

### Qualité

- [ ] Couverture tests > 80%
- [ ] Tous les tests passent (vert)
- [ ] Tests d'intégration validés
- [ ] Tests de performance acceptables
- [ ] Tests de sécurité validés
- [ ] Bugs critiques corrigés
- [ ] Bugs majeurs corrigés

### Documentation

- [ ] README.md à jour
- [ ] ARCHITECTURE.md complété
- [ ] API.md documenté
- [ ] DEPLOIEMENT.md écrit
- [ ] UTILISATION.md écrit
- [ ] CHANGELOG.md créé

### Production

- [ ] Configuration production prête
- [ ] Sauvegardes configurées et testées
- [ ] Monitoring actif
- [ ] Équipe formée
- [ ] Validation métier obtenue

---

## ESTIMATION GLOBALE

### Par phase

| Phase | Durée | Charge (jours/homme) |
|-------|-------|----------------------|
| Phase 1 – Modules Moteurs | 4-6 semaines | 20-30 jours |
| Phase 2 – API REST | 3-4 semaines | 15-20 jours |
| Phase 3 – E-commerce | 2-3 semaines | 10-15 jours |
| Phase 4 – Tests | 2-3 semaines | 10-15 jours |
| Phase 5 – Finalisation | 1 semaine | 5 jours |
| **TOTAL** | **12-17 semaines** | **60-85 jours** |

### Par module (détail Phase 1)

| Module | Tâches | Durée estimée |
|--------|--------|---------------|
| Facturation | 8 tâches | 2-3 semaines |
| Caisse | 10 tâches | 2-3 semaines |
| Approvisionnements | 8 tâches | 2-3 semaines |

### Ressources nécessaires

**Équipe recommandée :**
- 1 Chef de projet / Architecte (temps partiel)
- 2 Développeurs backend Django (temps plein)
- 1 Développeur frontend (temps partiel, pour corrections boutique)
- 1 DevOps (temps partiel, pour déploiement)

**Environnement :**
- Serveur de développement (local)
- Serveur de test (staging)
- Serveur de production
- Accès Firebase (projet Conbuska)
- Accès base de données (PostgreSQL)

**Outils :**
- Git (versioning)
- GitHub/GitLab (collaboration)
- pytest (tests)
- Postman/Insomnia (tests API)
- Sentry (monitoring erreurs)
- Prometheus + Grafana (monitoring métriques)

---

## PROCHAINES ÉTAPES

1. **Valider ce plan** avec l'équipe et le métier
2. **Créer la structure de dossiers** (PHASE1_MODULES_MOTEURS/, etc.)
3. **Commencer Phase 1.1 – Facturation** (module le plus critique)
4. **Suivre la checklist** tâche par tâche
5. **Commit réguliers** (après chaque tâche validée)
6. **Revue de code** hebdomadaire
7. **Démonstration** au métier toutes les 2 semaines

---

## CONTACT ET SUPPORT

**Responsable projet :** [À définir]  
**Architecte technique :** Cline (IA)  
**Équipe développement :** [À définir]  
**Contact métier :** Ets La Lumière

**Document associé :**
- AUDIT_CONBUSKA.md (rapport d'audit complet)
- ARCHITECTURE.md (architecture technique)
- README.md (guide d'installation)

---

**Document validé par :** _________________  
**Date :** _________________  
**Signature :** _________________