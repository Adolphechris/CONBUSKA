# AUDIT PARTIE 1/5 - MODULES CORE + PAIE

## Module PAIE - Analyse caractère par caractère

### Fichier: paie/models.py (167 lignes) ✅
- Agent: matricule(IntegerField), nom, date_naissance, date_engagement, photo, email, adresse, telephone, ville, poste, departement, type_contrat, salaire, actif, date_creation, date_modification → ✅
- Problème: `unique=True` sur `nom` ET `email` → peut bloquer si deux agents homonymes ou email partagé
- Paie: mois, agent(FK), salaire_base, jap, jp, absence, salaire_brut, total_primes, total_retenues, net_a_payer, taux_creation, valeur_usd, valide, cree_par, modifie_par → ✅
- Contrainte `unique_together = [('agent', 'mois')]` → ✅
- LignePaie: paie(FK), libelle, type_ligne, montant, ordre, valeur_usd, taux_creation → ✅

### Fichier: paie/inputs.py (52 lignes) ❌ BUG
- AgentCreateInput: nom, date_naissance, date_engagement, adresse, telephone, ville, salaire, poste, departement, type_contrat, email → **MANQUE matricule**
- AgentUpdateInput: agent_id, nom, ..., email → ✅ mais pas de matricule non plus (normal ici)
- PaieCreateInput: agent_id, mois, jap=26, jp=26, absence=0 → ✅

### Fichier: paie/services.py (633 lignes) ❌ 3 BUGS
- Ligne 36-50: `_calculer_cnss()` → plafond 500000 FC, taux 5% → ✅
- Ligne 53-73: `_calculer_ipr()` → barème progressif 0-20% → ✅
- Ligne 76-101: `_calculer_prime_anciennete()` → 2%/3%/5% par an → ✅ mais **pas de plafond**
- Ligne 106-270: `calculer_bulletin()` → ⚠️ PRENDS agent.date_engagement au lieu de la date de paie pour le calcul d'ancienneté
- Ligne 437-460: `creer_agent()` → **BUG CRITIQUE** ligne 447: `matricule=data.matricule` → data n'a PAS de matricule
- Ligne 520-563: `valider_paie()` → **BUG** try/except Exception as e: pass (avale tout)
- Ligne 563: `return PaieValidationResult(paie=paie, warning=None)` → **BUG** manque `mouvement_caisse_cree`
- Ligne 584-586: `PaieValidationResult` → seulement paie, warning

### Fichier: paie/views.py (373 lignes) ✅
- AgentsView, AgentDetailsView, AgentCreateView, AgentUpdateView, AgentDeleteView → ✅
- AgentCreateView ligne 110: `type_contrat=cd.get('type_contrat') or ''` → **ATTENTION**: AgentCreateInput attend `type_contrat: str = TypeContrat.CDI`, la vue passe '' par défaut
- PaieAgentCreateView, PaieAgentDetailsView, PaieAgentDeleteView, PaieValiderView → ✅
- PaiePdfView → utilise DocumentGenerator → non vérifié
- ListePaiesView → ✅ avec dual currency

### Fichier: paie/exceptions.py (29 lignes) ✅
- PaieError, AgentDejaExisteError, AgentInactifError, PaieDejaExistanteError, PaieDejaValideeError, CaissePrincipaleFermeeError → ✅

### Fichier: paie/tests.py (3 lignes) ❌ PLACEHOLDER VIDE
- Masque le dossier paie/tests/ qui contient les VRAIS tests

### Dossier: paie/tests/ ✅ tests bien écrits (mais inaccessibles)
- test_services.py (363 lignes): 21 tests
- test_selectors.py: tests des selecteurs
- factories.py: factories factory-boy

### ANOMALIES PAIE DÉTECTÉES:
1. ❌ `creer_agent()` utilise data.matricule mais AgentCreateInput n'a pas matricule
2. ❌ `valider_paie()` avale les exceptions (pass)
3. ❌ `PaieValidationResult` manque `mouvement_caisse_cree` attendu par les tests
4. ⚠️ `_calculer_prime_anciennete()` pas de plafond (peut dépasser 100% pour >20 ans)
5. ⚠️ `calculer_bulletin()` utilise agent.date_engagement pour le calcul d'ancienneté
6. ❌ `paie/tests.py` vide masque `paie/tests/`

---

## Module CAISSE - Analyse caractère par caractère

### Fichier: caisse/models.py (450 lignes) ✅✅✅
- Caisse, CaisseCourante, RubriqueCaisse, SousRubriqueCaisse → ✅ avec dual currency
- MouvementCaisse + 7 tables de liaison (Fournisseur, Client, Creancier, Debiteur, Agent, ChargesExploitation, ChargesPersonnelles) → ✅
- Chaque table de liaison a `valeur_usd` et `taux_paiement`/`taux_mouvement` → ✅
- Chaque save() vérifie l'immutabilité des champs historiques → ✅
- **ANOMALIE**: MouvementCaisse a `montant_usd` + `taux_mouvement` MAIS les tables de liaison ont `valeur_usd` + `taux_paiement` → deux noms différents pour la même chose

### Fichier: caisse/services/mouvement_caisse.py (459 lignes) ✅✅✅
- MouvementCaisseService complet avec create, update, delete, dispatch, transfert
- Guards: _assert_caisse_ouverte, _assert_solde_suffisant, _assert_not_mirror
- Rebuild impacts avec SnapshotService et FondsRoulementService
- Dispatch: fournisseur, client, creancier, debiteur, agent, charge, transfert
- **ANOMALIE**: `_assert_solde_suffisant` ligne 57-70 ne prend en compte que les entrées, pas les sorties déjà existantes
- **ANOMALIE**: `_cleanup_transfert` ligne 100-104 supprime le miroir sans rebuild

### Fichier: caisse/tests.py (non lu complètement) ✅ 15/15 tests

---

## Module FACTURES - Analyse caractère par caractère

### Fichier: factures/models.py (197 lignes) ✅
- Livreur, Facture, DetailsFacture, FactureClient → ✅
- Facture: numero, date_facture, devise, taux, remise, client_comptoir, livreur, cree_par, modifie_par, actif, valide, valeur_usd → ✅
- Propriétés: sous_total, total, total_devise, total_articles → calculs corrects
- `clean()`: vérifie cohérence devise/taux/valeur_usd pour factures validées → ✅
- DetailsFacture: facture(FK), article(FK), qte, prix, valeur_usd, taux_creation → ✅
- FactureClient: facture(OneToOne), client(FK) → ✅

### ANOMALIES FACTURES:
- ⚠️ `sous_total` (ligne 72-81) recalcule à chaque appel depuis la DB → pas de cache
- ⚠️ `client_comptoir` (CharField) vs FactureClient → deux manières de lier un client
- ⚠️ Pas de test pour Facture.clean() ni pour la validation des factures

---

## Module CLIENTS - Analyse caractère par caractère

### Fichier: clients/models.py (85 lignes) ✅
- Client: code, photo, nom, email, adresse, telephone, ville → ✅
- `factures()`, `paiements()`, `total_factures_usd()`, `total_paiements_usd()`, `solde_usd()`, `solde_fc()` → ✅
- `solde()` retourne `solde_usd()` → conforme à l'architecture dual currency
- `get_next_code` → génère code 3000+ → ✅

### ANOMALIES CLIENTS:
- ⚠️ `get_next_code` (ligne 69-75): pas de transaction.atomic, risque de doublon en concurrence

---

## Module FOURNISSEURS - Analyse caractère par caractère

### Fichier: fournisseurs/models.py (91 lignes) ✅
- Fournisseur: code, photo, nom, email, adresse, telephone, ville, pays, tuteur, rccm, id_nat, impot, tva, is_system, actif, type_frais → ✅
- `mouvements()`, `paiements()`, `total_mouvements_usd()`, `total_paiements_usd()`, `solde_usd()`, `solde_fc()` → ✅
- `solde()` retourne `solde_usd()` → ✅

### ANOMALIES FOURNISSEURS:
- ⚠️ `get_next_code` (ligne 75-80): pas de transaction.atomic non plus
- ⚠️ `is_system` booléen → logique spéciale dans `mouvements()` qui bifurque vers FraisApprovisionnement

---

## Module CREANCIERS/DEBITEURS - Analyse caractère par caractère

### Fichier: creanciers/models.py (139 lignes) ✅
- Creancier: code, photo, nom, email, adresse, telephone, ville → ✅
- Debiteur: idem → ✅
- Chacun: prets(), paiements(), solde_usd(), solde_fc(), solde()=solde_usd() → ✅
- Attention: pour Creancier, ENTRÉE = prêt, SORTIE = remboursement
- Pour Debiteur, l'inverse: SORTIE = prêt, ENTRÉE = remboursement
- `get_next_code()` utilise transaction.atomic avec select_for_update → ✅

### ANOMALIES CREANCIERS:
- ✅ `get_next_code` correctement implémenté avec transaction.atomic
- ⚠️ Pas de gestion des prêts avec intérêts

---

## Module APPROVISIONNEMENTS - Analyse caractère par caractère

### Fichier: approvisionnements/models.py (306 lignes) ✅
- TypeFrais, Approvisionnement, DetailsApprovisionnement, FraisApprovisionnement → ✅
- Approvisionnement: numero, magasin, devise, taux, cree_par, modifie_par, actif, valide → ✅
- `clean()`: vérifie immutabilité devise/taux pour appro validé → ✅
- `save()`: auto-numérotation, full_clean si valide → ✅
- DetailsApprovisionnement: fournisseur, facture, article, qte, prix, date_peremption, valeur_usd, taux_creation → ✅
- `add()`, `update_appro()`: logique de fusion avec gestion des dates de péremption → ✅ (bien fait)
- FraisApprovisionnement: type_frais, montant, valeur_usd, taux_creation → ✅

### ANOMALIES APPROVISIONNEMENTS:
- ⚠️ `prix_vente` (ligne 131-137) et `prix_vente_gros` (ligne 139-144) appellent `article.prix_vente_devise` qui fait une requête DB à chaque appel
- ⚠️ `résultat` (ligne 147-152) recalcule complètement sans cache

---

## Module COMMANDES - Analyse caractère par caractère

### Fichier: commandes/models.py (94 lignes) ✅
- Commande: numero, date_commande, fournisseur, devise(FK), taux, statut, cree_par, modifie_par, actif → ✅
- Statuts: BROUILLON, VALIDEE, TRANSFORMEE → ✅ (note: pas de 'ANNULEE')
- DetailsCommande: commande(FK), article(FK), qte, prix → ✅

### ANOMALIES COMMANDES:
- ⚠️ `devise` est un ForeignKey vers `parametres.Devise` → PAS un CharField comme dans Facture et Approvisionnement → INCOHÉRENCE
- ⚠️ Pas de `valeur_usd` ni `taux_creation` sur DetailsCommande → INCOHÉRENCE avec les autres modules
- ⚠️ Pas de dual currency dans commandes
- ⚠️ Statut 'ANNULEE' manquant

---

## Module PRODUITS - Analyse caractère par caractère

### Fichier: produits/models.py (309 lignes) ✅
- Categorie, Unite → simples
- Article: code, designation, description, categorie, unite, fournisseur, prix_achat, prix_vente, prix_vente_gros, devise, seuil, seuil_gros, emplacement, photo1, photo2, est_publie, slug, derniere_sync_firestore → ✅
- `stock` propriété → calcule via Sum sur Stock avec magasin principal → ✅
- `prix_vente_devise`, `prix_vente_gros_devise` → conversion dual currency → ✅
- Stock: magasin, article, qte, date_peremption → contrainte unique_lot_stock + qte_gte_0 → ✅
- MouvementStock: IN/OUT avec source_type/source_id → ✅
- TransfertStock: magasin_source/destination avec détails et réservation lots → ✅

### ANOMALIES PRODUITS:
- ⚠️ `code_barre` ligne 69 est commenté → code mort
- ⚠️ `prix_achat`, `prix_vente`, `prix_vente_gros` → DecimalField(max_digits=10) → risque de dépassement
- ⚠️ `stock` propriété (ligne 112-122) fait une requête Sum à chaque appel → pas de cache

---

## MODULE PARAMETRES - Analyse caractère par caractère

### Fichier: parametres/models.py (189 lignes) ✅
- Devise: code, nom, symbole, actif → ✅
- TauxEchangeManager: `get_rate_for_date()` → dernier taux connu → ✅
- `get_taux_usd_cdf()` → fallback 2500.00 si pas de taux → ✅
- Parametre: logo, sigle, societe, rccm, idnat, impot, tva, pays, adresse, ville, telephone, email → ✅
- Magasin: nom, description, is_principal, localisation → ✅
- TauxEchange: devise_source, devise_cible, taux, effective_date, modifie_par, history(HistoricalRecords) → ✅

### ANOMALIES PARAMETRES:
- ✅ TauxEchange avec historique complet (django-simple-history)
- ✅ Contrainte unique_rate_per_day
- ✅ Fallback sécurisé 2500.00

---

## RÉCAPITULATIF ANOMALIES CORE

### BLOQUANTES:
- [ ] PAIE: creer_agent() utilise data.matricule inexistant → CASSÉ
- [ ] PAIE: valider_paie() avale les exceptions → CASSÉ
- [ ] PAIE: PaieValidationResult manque mouvement_caisse_cree → CASSÉ
- [ ] PAIE: paie/tests.py vide masque les vrais tests → CASSÉ

### IMPORTANTES:
- [ ] COMMANDES: devise est FK (incohérent avec Facture/Appro)
- [ ] COMMANDES: pas de dual currency (valeur_usd/taux_creation)
- [ ] COMMANDES: pas de statut ANNULEE
- [ ] CLIENTS/FOURNISSEURS: get_next_code sans transaction
- [ ] CAISSE: montant_usd vs valeur_usd → noms différents pour même concept

### MINEURES:
- [ ] PAIE: prime_anciennete sans plafond
- [ ] PAIE: calcul_bulletin utilise date du jour pour ancienneté
- [ ] APPRO: prix_vente recalcule à chaque appel
- [ ] PRODUITS: code_barre commenté