# E-commerce - Phase 3

**Statut:** En attente  
**Priorité:** MOYENNE  
**Durée estimée:** 2-3 semaines

---

## Objectif

Finaliser la boutique e-commerce avec monitoring, tests et déploiement.

---

## Tâches à accomplir

### Tâche 3.1 – Cron jobs
- [ ] Synchronisation Firestore (toutes les 5 min)
- [ ] Nettoyage paniers abandonnés (toutes les heures)
- [ ] Mise à jour stock boutique (temps réel)
- **Test:** `test_cron_jobs.py`

### Tâche 3.2 – Monitoring
- [ ] Logs d'erreurs structurés
- [ ] Alertes email sur erreurs critiques
- [ ] Dashboard monitoring (Sentry/LogRocket)
- **Test:** Manuel

### Tâche 3.3 – Tests bout en bout
- [ ] Parcours complet: navigation → panier → commande → paiement
- [ ] Tests multi-devises
- [ ] Tests cas limites (stock épuisé, paiement échoué)
- **Test:** `test_bout_en_bout.py`

### Tâche 3.4 – Déploiement boutique
- [ ] Configuration production Nuxt
- [ ] Variables d'environnement
- [ ] Build optimisé
- [ ] Déploiement Vercel/Netlify
- **Test:** Manuel

---

## Critères de validation

- [ ] Cron jobs fonctionnels
- [ ] Monitoring actif
- [ ] Tests E2E passent
- [ ] Boutique déployée et accessible

---

## Fichiers concernés

- `boutique/` (application Nuxt)
- `ecommerce/sync/` (synchronisation)
- `ecommerce/tests/`