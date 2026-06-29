# Boutique Ets La Lumière

Application web Progressive Web App (PWA) pour la boutique en ligne Ets La Lumière.

## 🚀 Technologies

- **Framework**: Nuxt 3 (Vue 3)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **State Management**: Pinia
- **Database**: Firebase Firestore
- **Hosting**: Firebase Hosting
- **PWA**: @nuxtjs/pwa

## 📦 Installation

### Prérequis

- Node.js >= 18
- npm ou yarn
- Compte Firebase

### Étapes

1. **Cloner le projet**
   ```bash
   cd boutique
   ```

2. **Installer les dépendances**
   ```bash
   npm install
   ```

3. **Configurer les variables d'environnement**
   
   Copier le fichier `.env.example` vers `.env`:
   ```bash
   cp .env.example .env
   ```
   
   Remplir les variables Firebase:
   ```env
   VITE_FIREBASE_API_KEY=your_api_key
   VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your_project_id
   VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
   VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   VITE_FIREBASE_APP_ID=your_app_id
   VITE_IMAGE_DEFAUT_URL=/images/default-product.jpg
   VITE_SITE_URL=https://boutique.conbuska.cd
   VITE_APP_NAME=Ets La Lumière
   VITE_CURRENCY=CDF
   ```

4. **Ajouter les icônes PWA**
   
   Placer les icônes dans le dossier `public/`:
   - `icon-192x192.png` (192x192px)
   - `icon-512x512.png` (512x512px)
   - `images/default-product.jpg` (image par défaut)

## 🛠️ Développement

### Lancer le serveur de développement

```bash
npm run dev
```

L'application sera accessible sur `http://localhost:3000`

### Build pour la production

```bash
npm run build
```

### Prévisualiser le build

```bash
npm run preview
```

## 🚀 Déploiement sur Firebase Hosting

### Prérequis

- Installer Firebase CLI: `npm install -g firebase-tools`
- Se connecter: `firebase login`
- Initialiser le projet Firebase (une seule fois)

### Étapes de déploiement

1. **Initialiser Firebase Hosting** (première fois seulement)
   ```bash
   firebase init hosting
   ```
   - Sélectionner le projet Firebase existant
   - Configurer comme une application mono-page (SPA)
   - Ne pas écraser le fichier `index.html`

2. **Build de l'application**
   ```bash
   npm run build
   ```

3. **Déployer**
   ```bash
   firebase deploy --only hosting
   ```

4. **Configurer le domaine personnalisé** (optionnel)
   - Dans Firebase Console: Hosting > Ajouter un domaine personnalisé
   - Suivre les instructions pour configurer les DNS

## 📁 Structure du projet

```
boutique/
├── assets/
│   └── css/
│       └── main.css          # Styles globaux
├── components/
│   ├── AppFooter.vue         # Footer de l'application
│   ├── AppHeader.vue         # Header avec navigation et recherche
│   ├── BadgeStock.vue        # Badge de statut de stock
│   └── ProductCard.vue       # Carte produit
├── composables/
│   └── useFirebase.ts        # Composable pour Firebase
├── layouts/
│   └── default.vue           # Layout par défaut
├── pages/
│   ├── index.vue             # Page d'accueil
│   ├── categorie/
│   │   └── [nom].vue         # Liste produits par catégorie
│   ├── produit/
│   │   └── [code].vue        # Fiche produit détaillée
│   ├── panier.vue            # Panier d'achat
│   ├── checkout.vue          # Formulaire de commande
│   ├── confirmation.vue      # Page de confirmation
│   └── recherche.vue         # Résultats de recherche
├── plugins/
│   └── firebase.client.ts    # Plugin Firebase (client-side)
├── services/
│   └── firebase.ts           # Services Firebase
├── stores/
│   └── cart.ts               # Store Pinia pour le panier
├── types/
│   └── index.ts              # Types TypeScript
├── public/                   # Fichiers statiques
├── .env.example              # Variables d'environnement exemple
├── nuxt.config.ts            # Configuration Nuxt
└── package.json
```

## 🎨 Fonctionnalités

### Pour les visiteurs
- ✅ Catalogue de produits avec pagination (24 produits/page)
- ✅ Recherche de produits
- ✅ Filtrage par catégorie
- ✅ Fiche produit détaillée avec images
- ✅ Gestion du panier (ajout, modification, suppression)
- ✅ Passage de commande sans paiement en ligne
- ✅ PWA installable (mobile et desktop)
- ✅ Mode offline (catalogue consultable)

### Règles d'affichage
- **Stock vert**: En stock (> seuil_alerte)
- **Stock orange**: Plus que X en stock (0 < stock <= seuil_alerte)
- **Stock rouge**: Rupture de stock (stock = 0)

### SEO
- ✅ URLs propres et descriptives
- ✅ Meta tags dynamiques par page
- ✅ Open Graph tags
- ✅ Canonical URLs
- ✅ Données structurées JSON-LD (à implémenter)
- ✅ Sitemap.xml (à générer)

## 🔒 Sécurité

- Les commandes sont créées dans Firestore sans authentification
- Firebase App Check recommandé pour protéger contre le spam
- Règles Firestore à configurer pour autoriser les écritures dans `commandes_en_ligne`

## 📝 Configuration Firestore

### Structure des collections

**articles_publics** (catalogue)
```typescript
{
  code_article: string (ID du document)
  nom: string
  categorie: string
  prix: number
  stock_disponible: number
  image_url: string
  description?: string
  seuil_alerte: number
  date_mise_a_jour: timestamp
}
```

**commandes_en_ligne** (commandes clients)
```typescript
{
  date_commande: timestamp
  client: {
    nom: string
    email: string
    telephone?: string
    adresse?: string
  }
  lignes: [{
    code_article: string
    quantite: number
    prix_unitaire: number
    nom_article: string
  }]
  total: number
  statut: "nouveau"
}
```

## 🧪 Tests

```bash
# Tests unitaires (à implémenter)
npm run test

# Linter
npm run lint
```

## 📊 Performance

- Objectif Lighthouse: ≥ 90 sur toutes les catégories
- Images optimisées avec lazy loading
- Code splitting automatique par Nuxt
- PWA avec cache des images

## 🐛 Dépannage

### Erreur de compilation TypeScript
```bash
# Vider le cache Nuxt
rm -rf .nuxt node_modules/.cache
npm run dev
```

### Problème de variables d'environnement
- Vérifier que le fichier `.env` existe
- Redémarrer le serveur après modification de `.env`

### Firebase ne se connecte pas
- Vérifier les clés API dans `.env`
- Vérifier les règles Firestore
- Vérifier la console Firebase pour les erreurs

## 📄 Licence

Propriétaire - Ets La Lumière

## 👤 Contact

- Email: contact@etslalumiere.cd
- Téléphone: +242 XX XXX XXXX
- Adresse: Kinshasa, RDC

---

**Développé avec ❤️ pour Ets La Lumière**