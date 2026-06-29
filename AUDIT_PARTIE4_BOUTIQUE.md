# AUDIT PARTIE 4/5 - BOUTIQUE NUXT (FRONTEND)

## Structure du projet boutique/

```
boutique/
├── package.json          → Dépendances Nuxt 3
├── nuxt.config.ts        → Configuration Nuxt
├── vitest.config.ts      → Configuration tests
├── tsconfig.json
├── app.vue               → Point d'entrée
├── layouts/default.vue   → Layout principal
├── assets/css/main.css   → Styles
├── components/
│   ├── ProductCard.vue   → Carte produit
│   ├── BadgeStock.vue    → Badge stock
│   ├── AppHeader.vue     → Header
│   └── AppFooter.vue     → Footer
├── composables/
│   ├── useFirebase.ts    → Connexion Firebase
│   └── useJsonLd.ts      → Données structurées SEO
├── pages/
│   ├── index.vue         → Accueil
│   ├── panier.vue        → Panier
│   ├── checkout.vue      → Paiement
│   ├── confirmation.vue  → Confirmation
│   ├── recherche.vue     → Recherche
│   ├── a-propos.vue      → Pages statiques
│   ├── contact.vue
│   ├── livraison.vue
│   ├── faq.vue
│   ├── mentions-legales.vue
│   ├── politique-confidentialite.vue
│   ├── conditions-utilisation.vue
│   ├── categorie/[nom].vue  → Catégorie
│   └── produit/[code].vue   → Fiche produit
├── plugins/
│   └── firebase.client.ts   → Plugin Firebase
├── public/
│   ├── manifest.json     → PWA manifest
│   ├── sw.js             → Service Worker
│   ├── offline.html      → Page hors-ligne
│   └── robots.txt        → SEO
├── scripts/
│   └── generate-sitemap.js → Générateur sitemap
├── services/
│   ├── firebase.ts       → Service Firebase
│   └── api.ts            → API Conbuska
├── stores/
│   └── cart.ts           → Store panier (Pinia)
├── types/
│   └── index.ts          → Types TypeScript
└── tests/
    ├── components/
    │   ├── ProductCard.spec.ts  → Tests composant
    │   └── BadgeStock.spec.ts
    └── stores/
        └── cart.spec.ts         → Tests store
```

## Analyse par fichier

### package.json ✅
- Nuxt 3, Pinia, Firebase, Vitest, TypeScript
- Dépendances complètes

### nuxt.config.ts ✅
- Configuration SSR, PWA, SEO, Firebase

### Components ✅
- ProductCard.vue: affiche nom, prix, stock, badge, image
- BadgeStock.vue: badge "En stock", "Faible stock", "Rupture"
- AppHeader.vue: navigation, panier
- AppFooter.vue: liens, contact

### Pages ✅
- index.vue: accueil avec catégories et produits
- panier.vue: gestion du panier
- checkout.vue: formulaire de commande
- confirmation.vue: confirmation après commande
- recherche.vue: recherche textuelle
- Pages statiques: a-propos, contact, livraison, faq, mentions-legales, politique-confidentialite, conditions-utilisation
- categorie/[nom].vue: filtrage par catégorie
- produit/[code].vue: fiche détaillée

### Stores ✅
- cart.ts: store Pinia avec localStorage, ajout/suppression/quantité

### Tests ✅
- ProductCard.spec.ts: test unitaire composant
- BadgeStock.spec.ts: test unitaire badge
- cart.spec.ts: test store panier

### PWA ✅
- manifest.json: icônes, thème, nom
- sw.js: service worker offline
- offline.html: page hors-ligne

### SEO ✅
- robots.txt
- generate-sitemap.js
- useJsonLd.ts: données structurées JSON-LD

## ANOMALIES BOUTIQUE

### IMPORTANTES:
- ⚠️ `produit/[code].vue` utilise le CODE comme paramètre, mais ARCHITECTURE.md dit SLUG → INCOHÉRENCE
- ⚠️ Pas de test e2e (Playwright config existe mais pas de tests écrits)
- ⚠️ Pas de test pour les pages (checkout, panier, etc.)

### MINEURES:
- ⚠️ Pas de gestion d'erreur Firebase visible dans les composants
- ⚠️ Pas de page 404 personnalisée
- ⚠️ Pas de page "catégorie vide"