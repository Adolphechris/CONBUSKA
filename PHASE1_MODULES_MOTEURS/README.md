# Modules Moteurs - Phase 1

**Statut:** En cours  
**Priorité:** CRITIQUE  
**Durée estimée:** 4-6 semaines

---

## Objectif

Développer les 3 modules cœur du système : Facturation, Caisse, Approvisionnements.

---

## Structure

```
PHASE1_MODULES_MOTEURS/
├── 1.1_FACTURATION/
│   ├── README.md
│   ├── checklist.md
│   └── tests/
├── 1.2_CAISSE/
│   ├── README.md
│   ├── checklist.md
│   └── tests/
└── 1.3_APPROVISIONNEMENTS/
    ├── README.md
    ├── checklist.md
    └── tests/
```

---

## Modules

### 1.1 Facturation
- Validation stock par lots ✅
- Calcul coût par lot (PAS DE MOYENNE)
- Mise à jour stock
- Génération écriture caisse
- Annulation contrôlée (contre-écriture)
- Double devise USD/FC
- Journalisation

### 1.2 Caisse
- Structure hiérarchique
- Règle bloquante solde insuffisant
- Transferts inter-caisses
- 7 types d'entrées
- 6 catégories de sorties
- Intégrations modules
- Double devise

### 1.3 Approvisionnements
- Services métier
- Répartition frais (7 services)
- Création lots avec coûts individuels
- Mise à jour stock
- Gestion dettes fournisseurs
- Double devise
- Intégration caisse

---

## Principe Fondamental

**PAS DE COÛT DE REVIENT MOYEN**

Chaque lot garde son propre coût d'achat. Traçabilité totale par approvisionnement.

---

## Ordre d'exécution

1. **1.1 Facturation** (priorité maximale)
2. **1.2 Caisse** (parallèle possible)
3. **1.3 Approvisionnements** (après caisse)

---

## Critères de validation globaux

- [ ] Tous les tests passent (couverture > 80%)
- [ ] Intégrations entre modules fonctionnelles
- [ ] Double devise opérationnelle
- [ ] Documentation à jour