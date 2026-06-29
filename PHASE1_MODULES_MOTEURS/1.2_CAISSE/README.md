# Module Caisse - Phase 1.2

**Statut:** En cours  
**Priorité:** CRITIQUE  
**Durée estimée:** 4-6 semaines

---

## Objectif

Rendre le module de caisse complet avec hiérarchie, transferts inter-caisses, et règle bloquante de solde.

---

## Tâches à accomplir

### Tâche 1.2.1 – Structure hiérarchique des caisses
- [ ] Modèle Caisse: ajouter champ `caisse_parent`
- [ ] Types: principale, secondaire, virtuelle
- [ ] Vue arborescente
- **Test:** `test_structure_hierarchique.py`

### Tâche 1.2.2 – Règle bloquante (solde insuffisant)
- [ ] Vérifier solde avant toute sortie
- [ ] Lever erreur si solde insuffisant
- **Test:** `test_regle_bloquante.py`

### Tâche 1.2.3 – Transferts inter-caisses
- [ ] Créer transfert entre caisses
- [ ] Débiter caisse source
- [ ] Créditer caisse destination
- [ ] Traçabilité complète
- **Test:** `test_transferts_inter_caisses.py`

### Tâche 1.2.4 – 7 types d'entrées
- [ ] vente, approvisionnement, apport_capital, emprunt, autre_entree
- **Test:** `test_types_entrees.py`

### Tâche 1.2.5 – 6 catégories de sorties
- [ ] charges_exploitation, salaires, fournisseurs, impots, autre_sortie
- **Test:** `test_categories_sorties.py`

### Tâche 1.2.6 – Intégration avec factures
- [ ] Génération automatique lors validation facture
- **Test:** `test_integration_factures.py`

### Tâche 1.2.7 – Intégration avec approvisionnements
- [ ] Enregistrement paiement fournisseurs
- **Test:** `test_integration_approvisionnements.py`

### Tâche 1.2.8 – Intégration avec paie
- [ ] Enregistrement salaires
- **Test:** `test_integration_paie.py`

### Tâche 1.2.9 – Double devise USD/FC
- [ ] Tous montants en USD et FC
- **Test:** `test_double_devise_caisse.py`

### Tâche 1.2.10 – Journalisation audit_log
- [ ] Logger tous les mouvements
- **Test:** `test_journalisation_caisse.py`

---

## Critères de validation

- [ ] Tous les tests passent (couverture > 80%)
- [ ] Transferts inter-caisses fonctionnels
- [ ] Règle bloquante opérationnelle
- [ ] Double devise OK

---

## Fichiers concernés

- `caisse/services/mouvement_caisse.py`
- `caisse/models.py`
- `caisse/views.py`
- `caisse/forms.py`
- `caisse/selectors.py`
- `caisse/tests.py`