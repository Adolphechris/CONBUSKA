# API REST - Phase 2

**Statut:** En attente  
**Priorité:** MOYENNE  
**Durée estimée:** 3-4 semaines

---

## Objectif

Développer une API REST complète pour intégrations externes et future application mobile.

---

## Tâches à accomplir

### Tâche 2.1 – Authentification JWT
- [ ] Configuration djangorestframework-simplejwt
- [ ] Endpoints login/refresh/token
- [ ] Permissions par rôle
- **Test:** `test_authentification_jwt.py`

### Tâche 2.2 – Pagination et filtres
- [ ] Pagination globale (100 items/page)
- [ ] Filtres par date, montant, statut
- [ ] Recherche full-text
- **Test:** `test_pagination_filtres.py`

### Tâche 2.3 – Endpoints Factures
- [ ] GET /api/factures/ (liste)
- [ ] POST /api/factures/ (création)
- [ ] GET /api/factures/{id}/ (détail)
- [ ] PUT /api/factures/{id}/ (modification)
- [ ] DELETE /api/factures/{id}/ (annulation)
- **Test:** `test_endpoints_factures.py`

### Tâche 2.4 – Endpoints Caisse
- [ ] GET /api/caisse/mouvements/
- [ ] POST /api/caisse/entree/
- [ ] POST /api/caisse/sortie/
- [ ] GET /api/caisse/transferts/
- **Test:** `test_endpoints_caisse.py`

### Tâche 2.5 – Endpoints Approvisionnements
- [ ] GET /api/approvisionnements/
- [ ] POST /api/approvisionnements/
- [ ] GET /api/approvisionnements/{id}/lots/
- **Test:** `test_endpoints_approvisionnements.py`

### Tâche 2.6 – Endpoints Produits
- [ ] GET /api/produits/
- [ ] GET /api/produits/{id}/stock/
- [ ] GET /api/produits/{id}/lots/
- **Test:** `test_endpoints_produits.py`

### Tâche 2.7 – Permissions RBAC
- [ ] Rôles: admin, caissier, magasinier, comptable, lecteur
- [ ] Permissions par endpoint
- **Test:** `test_permissions_rbac.py`

### Tâche 2.8 – Rate Limiting
- [ ] Limite: 100 req/min par utilisateur
- [ ] Limite: 1000 req/min par IP
- **Test:** `test_rate_limiting.py`

### Tâche 2.9 – Documentation Swagger
- [ ] Configuration drf-yasg
- [ ] Endpoint /api/docs/
- [ ] Schémas OpenAPI
- **Test:** Manuel

### Tâche 2.10 – Tests d'intégration
- [ ] Tests bout en bout API
- [ ] Tests de charge (1000 req/s)
- **Test:** `test_integration_api.py`

---

## Critères de validation

- [ ] 50+ endpoints fonctionnels
- [ ] Tests passent (couverture > 80%)
- [ ] Documentation Swagger accessible
- [ ] Performance < 200ms par requête

---

## Fichiers concernés

- `api/serializers.py`
- `api/views.py`
- `api/urls.py`
- `api/permissions.py`
- `api/throttles.py`