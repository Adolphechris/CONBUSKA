# Module Approvisionnements - Phase 1.3

**Statut:** En cours  
**Priorité:** CRITIQUE  
**Durée estimée:** 4-6 semaines

---

## Objectif

Rendre le module d'approvisionnements complet avec gestion des lots, coûts individuels, et répartition des frais.

## Principe Fondamental

**PAS DE COÛT DE REVIENT MOYEN** - Chaque approvisionnement a ses propres coûts (PAN, FA, PVD, PVG) par lot.

---

## Tâches à accomplir

### Tâche 1.3.1 – Services métier
- [ ] Créer ApprovisionnementService
- [ ] Créer DetailsApprovisionnementService
- [ ] Validation métier complète
- **Test:** `test_services_metier.py`

### Tâche 1.3.2 – Répartition frais (7 services)
- [ ] Frais transport (au poids/volume)
- [ ] Frais douane (par article)
- [ ] Frais assurance (par valeur)
- [ ] Frais manutention (par quantité)
- [ ] Frais stockage (par durée)
- [ ] Frais qualité (par contrôle)
- [ ] Frais divers (au prorata)
- **Test:** `test_repartition_frais.py`

### Tâche 1.3.3 – Création lots avec coûts individuels
- [ ] Créer Stock (lot) pour chaque ligne
- [ ] Enregistrer PAN, FA, PVD, PVG par lot
- [ ] Calculer coût total lot = PAN + FA + PVD + PVG
- [ ] PAS DE MOYENNE entre lots
- **Test:** `test_creation_lots_couts.py`

### Tâche 1.3.4 – Mise à jour stock
- [ ] Créer MouvementStock "entree_approvisionnement"
- [ ] Incrémenter quantité article
- [ ] Marquer lot avec date péremption
- **Test:** `test_mise_a_jour_stock_appro.py`

### Tâche 1.3.5 – Gestion dettes fournisseurs
- [ ] Créer DetteFournisseur
- [ ] Enregistrer montant total
- [ ] Suivi paiements
- **Test:** `test_dettes_fournisseurs.py`

### Tâche 1.3.6 – Validation avec double devise
- [ ] Montants en USD et FC
- [ ] Taux historique
- **Test:** `test_double_devise_appro.py`

### Tâche 1.3.7 – Intégration caisse
- [ ] Générer MouvementCaisse "sortie" lors paiement
- **Test:** `test_integration_caisse.py`

### Tâche 1.3.8 – Journalisation
- [ ] Logger création, validation, paiement
- **Test:** `test_journalisation_appro.py`

---

## Critères de validation

- [ ] Tous les tests passent (couverture > 80%)
- [ ] Lots créés avec coûts individuels
- [ ] Répartition frais correcte
- [ ] Dettes fournisseurs trackées

---

## Fichiers concernés

- `approvisionnements/services/`
- `approvisionnements/models.py`
- `approvisionnements/views.py`
- `approvisionnements/forms.py`
- `approvisionnements/tests.py`