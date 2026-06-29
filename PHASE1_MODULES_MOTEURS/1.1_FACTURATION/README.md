# Module Facturation - Phase 1.1

**Statut:** En cours  
**Priorité:** CRITIQUE  
**Durée estimée:** 4-6 semaines

---

## Objectif

Rendre le module de facturation complet et fonctionnel avec gestion des lots, double devise, et traçabilité totale.

## Principe Fondamental

**PAS DE COÛT DE REVIENT MOYEN** - Chaque lot garde son propre coût d'achat (PAN + FA + PVD + PVG).

---

## Tâches à accomplir

### Tâche 1.1.1 – Validation stock par lots ✅
- [x] Vérifier que chaque ligne référence un lot spécifique
- [x] Vérifier quantité disponible dans le lot
- [x] FIFO automatique par date péremption
- [x] Lever erreur si stock insuffisant
- **Test:** `test_validation_stock_lots.py` ✅ 7 tests passants

### Tâche 1.1.2 – Calcul coût par lot (PAS DE MOYENNE)
- [ ] Récupérer coût d'achat du lot spécifique
- [ ] Calculer coût total ligne = coût_lot × quantite
- [ ] Calculer marge = (PVD × quantite) - (coût_lot × quantite)
- [ ] Enregistrer coût dans LigneFacture
- **Test:** `test_cout_par_lot.py`

### Tâche 1.1.3 – Mise à jour stock lors validation
- [ ] Décrémenter quantité du lot vendu
- [ ] Créer MouvementStock "sortie_vente"
- [ ] Mettre à jour stock total article
- [ ] Marquer lot épuisé si nécessaire
- **Test:** `test_mise_a_jour_stock_validation.py`

### Tâche 1.1.4 – Génération écriture caisse automatique
- [ ] Créer MouvementCaisse lors validation
- [ ] Type: "vente" (entrée)
- [ ] Montant: total TTC facture
- [ ] Référence: numéro facture
- **Test:** `test_generation_caisse_validation.py`

### Tâche 1.1.5 – Mise à jour solde client
- [ ] Si client maison: incrémenter solde_client
- [ ] Si client comptoir: pas de solde (payé comptant)
- **Test:** `test_mise_a_jour_solde_client.py`

### Tâche 1.1.6 – Annulation contrôlée (contre-écriture)
- [ ] Créer FactureAnnulation liée à facture originale
- [ ] Copier lignes avec quantités négatives
- [ ] Remettre en stock les lots
- [ ] Créer MouvementCaisse "sortie_annulation"
- **Test:** `test_contre_ecriture_complete.py`

### Tâche 1.1.7 – Gestion double devise
- [ ] Montants en USD et FC
- [ ] Taux depuis parametres
- [ ] Conversion automatique
- **Test:** `test_double_devise.py`

### Tâche 1.1.8 – Journalisation audit_log
- [ ] Logger création, validation, annulation
- **Test:** `test_journalisation.py`

---

## Critères de validation

- [ ] Tous les tests passent (couverture > 80%)
- [ ] Manuel de test exécuté avec succès
- [ ] Documentation API à jour

---

## Fichiers concernés

- `factures/services/facture_service.py`
- `factures/models.py`
- `factures/views.py`
- `factures/forms.py`
- `factures/urls.py`
- `factures/tests/`