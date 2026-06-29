# 🎯 PLAN DE FINALISATION - Sprint 3

**Objectif**: Passer de 9/10 à 10/10 et avoir une implémentation parfaite.

---

## 📊 POURQUOI 9/10 ET PAS 10/10 ?

### Points manquants pour 10/10

| # | Point | Impact | Bloquant ? |
|---|-------|--------|------------|
| 1 | **PWA complète** (Service Worker + Cache) | Élevé | ⏳ Non |
| 2 | **Tests automatisés** (Vitest) | Moyen | ⏳ Non |
| 3 | **JSON-LD** (données structurées) | Moyen | ⏳ Non |
| 4 | **Sitemap.xml** automatique | Moyen | ⏳ Non |
| 5 | **robots.txt** | Faible | ⏳ Non |

**Pourquoi non-bloquants ?**
- L'application fonctionne et peut être déployée
- Ces éléments sont des **améliorations** et non des bugs
- Ils peuvent être ajoutés après le déploiement initial

---

## 🚀 PLAN D'ACTION POUR 10/10

### Phase 1: PWA Complète (30 min)

#### 1.1 Réactiver le module PWA
```bash
cd boutique
npm install @nuxtjs/pwa@latest
```

#### 1.2 Configurer nuxt.config.ts
```typescript
modules: [
  '@nuxtjs/tailwindcss',
  '@nuxtjs/pwa',
  '@pinia/nuxt'
],

pwa: {
  manifest: {
    name: 'Boutique Ets La Lumière',
    short_name: 'Conbuska',
    description: 'Boutique en ligne Ets La Lumière',
    theme_color: '#f97316',
    background_color: '#ffffff',
    display: 'standalone',
    start_url: '/',
    icons: [
      { src: '/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { src: '/icon-512x512.png', sizes: '512x512', type: 'image/png' }
    ]
  },
  workbox: {
    navigateFallback: '/',
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/firebasestorage\.googleapis\.com\/.*/i,
        handler: 'CacheFirst',
        options: {
          cacheName: 'firebase-images',
          expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 * 30 }
        }
      }
    ]
  }
}
```

#### 1.3 Créer les icônes PWA
- Générer `icon-192x192.png` (192x192px)
- Générer `icon-512x512.png` (512x512px)
- Placer dans `/boutique/public/`

**Outil**: https://favicon.io/ ou https://www.pwabuilder.com/

---

### Phase 2: Tests Automatisés (45 min)

#### 2.1 Installer Vitest
```bash
cd boutique
npm install -D vitest @vue/test-utils happy-dom
```

#### 2.2 Créer vitest.config.ts
```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'happy-dom',
    globals: true
  }
})
```

#### 2.3 Créer les tests

**tests/components/ProductCard.spec.ts**
```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ProductCard from '~/components/ProductCard.vue'

describe('ProductCard', () => {
  it('affiche le nom du produit', () => {
    const article = {
      code_article: 'TEST001',
      nom: 'Produit Test',
      categorie: 'Test',
      prix: 10000,
      stock_disponible: 10,
      image_url: '/test.jpg',
      seuil_alerte: 5
    }
    
    const wrapper = mount(ProductCard, {
      props: { article }
    })
    
    expect(wrapper.text()).toContain('Produit Test')
  })
  
  it('désactive le bouton si stock = 0', () => {
    const article = {
      code_article: 'TEST001',
      nom: 'Produit Test',
      categorie: 'Test',
      prix: 10000,
      stock_disponible: 0,
      image_url: '/test.jpg',
      seuil_alerte: 5
    }
    
    const wrapper = mount(ProductCard, {
      props: { article }
    })
    
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })
})
```

**tests/stores/cart.spec.ts**
```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCartStore } from '~/stores/cart'

describe('Cart Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })
  
  it('ajoute un article au panier', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    expect(cart.items.length).toBe(1)
    expect(cart.totalItems).toBe(1)
  })
  
  it('incrémente la quantité si article existe', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    expect(cart.items[0].quantite).toBe(2)
  })
})
```

#### 2.4 Ajouter les scripts dans package.json
```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run"
  }
}
```

---

### Phase 3: JSON-LD (20 min)

#### 3.1 Créer un composable useJsonLd.ts
```typescript
// composables/useJsonLd.ts
export const useJsonLd = () => {
  const addProductJsonLd = (article: any, prix: number, devise: string) => {
    const config = useRuntimeConfig()
    
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: article.nom,
      description: article.description || '',
      image: article.image_url,
      offers: {
        '@type': 'Offer',
        price: prix,
        priceCurrency: devise,
        availability: article.stock_disponible > 0 
          ? 'https://schema.org/InStock' 
          : 'https://schema.org/OutOfStock'
      }
    }
    
    useHead({
      script: [
        {
          type: 'application/ld+json',
          children: JSON.stringify(jsonLd)
        }
      ]
    })
  }
  
  const addOrganizationJsonLd = () => {
    const config = useRuntimeConfig()
    
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: 'Ets La Lumière',
      url: config.public.siteUrl,
      logo: `${config.public.siteUrl}/logo.png`
    }
    
    useHead({
      script: [
        {
          type: 'application/ld+json',
          children: JSON.stringify(jsonLd)
        }
      ]
    })
  }
  
  return {
    addProductJsonLd,
    addOrganizationJsonLd
  }
}
```

#### 3.2 Intégrer dans pages/produit/[code].vue
```typescript
const { addProductJsonLd } = useJsonLd()

watch(article, (newArticle) => {
  if (newArticle) {
    const config = useRuntimeConfig()
    addProductJsonLd(newArticle, newArticle.prix, config.public.currency)
  }
}, { immediate: true })
```

#### 3.3 Intégrer dans pages/index.vue
```typescript
const { addOrganizationJsonLd } = useJsonLd()

onMounted(() => {
  addOrganizationJsonLd()
})
```

---

### Phase 4: Sitemap & robots.txt (20 min)

#### 4.1 Créer un script de génération de sitemap
```javascript
// scripts/generate-sitemap.js
import { initializeApp } from 'firebase/app'
import { getFirestore, collection, getDocs } from 'firebase/firestore'
import { writeFileSync } from 'fs'

const firebaseConfig = {
  apiKey: process.env.VITE_FIREBASE_API_KEY,
  authDomain: process.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: process.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.VITE_FIREBASE_APP_ID
}

const app = initializeApp(firebaseConfig)
const db = getFirestore(app)

async function generateSitemap() {
  const baseUrl = 'https://boutique.conbuska.cd'
  
  // Récupérer tous les articles
  const articlesRef = collection(db, 'articles_publics')
  const snapshot = await getDocs(articlesRef)
  
  let urls = []
  
  // Pages statiques
  urls.push(`  <url>
    <loc>${baseUrl}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>`)
  
  urls.push(`  <url>
    <loc>${baseUrl}/panier</loc>
    <changefreq>weekly</changefreq>
    <priority>0.5</priority>
  </url>`)
  
  // Pages produits
  snapshot.docs.forEach(doc => {
    const data = doc.data()
    urls.push(`  <url>
    <loc>${baseUrl}/produit/${doc.id}</loc>
    <lastmod>${data.date_mise_a_jour?.toDate().toISOString() || new Date().toISOString()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>`)
  })
  
  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join('\n')}
</urlset>`
  
  writeFileSync('./public/sitemap.xml', sitemap)
  console.log('✅ Sitemap généré:', urls.length + 2, 'URLs')
}

generateSitemap().catch(console.error)
```

#### 4.2 Créer robots.txt
```
User-agent: *
Allow: /

# Sitemap
Sitemap: https://boutique.conbuska.cd/sitemap.xml

# Désactiver les répertoires sensibles
Disallow: /api/
Disallow: /admin/
```

#### 4.3 Ajouter au package.json
```json
{
  "scripts": {
    "generate:sitemap": "node scripts/generate-sitemap.js"
  }
}
```

---

### Phase 5: Règles Firestore (15 min)

#### 5.1 Créer firestore.rules complet
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Articles publics: lecture seule pour tous
    match /articles_publics/{article} {
      allow read: if true;
      allow write: if false; // Seul le backend Python écrit
    }
    
    // Commandes en ligne: écriture pour tous (sans auth)
    match /commandes_en_ligne/{commande} {
      allow read: if false;
      allow create: if request.auth == null 
                    && request.resource.data.client.nom is string
                    && request.resource.data.client.email is string
                    && request.resource.data.client.email.matches('^[^@]+@[^@]+\\.[^@]+$')
                    && request.resource.data.lignes is list
                    && request.resource.data.total is number
                    && request.resource.data.statut == 'nouveau';
      allow update, delete: if false;
    }
  }
}
```

#### 5.2 Déployer les règles
```bash
firebase deploy --only firestore:rules
```

---

### Phase 6: Tests Manuels (30 min)

#### 6.1 Checklist de test

**Flux complet:**
- [ ] Accueil charge les produits vedettes
- [ ] Catégories s'affichent correctement
- [ ] Clic catégorie → liste produits
- [ ] Pagination fonctionne (page 1, 2, 3...)
- [ ] Clic produit → fiche détaillée
- [ ] Image, prix, stock s'affichent
- [ ] "Ajouter au panier" fonctionne
- [ ] Panier se met à jour
- [ ] Modifier quantité (+/-)
- [ ] Supprimer article
- [ ] Checkout: formulaire s'affiche
- [ ] Validation: nom et email requis
- [ ] Soumission: commande créée dans Firestore
- [ ] Redirection vers confirmation
- [ ] Panier vidé après commande

**Responsive:**
- [ ] Mobile (375px): header, grille 1 colonne
- [ ] Tablette (768px): grille 2-3 colonnes
- [ ] Desktop (1024px+): grille 4 colonnes
- [ ] Navigation tactile OK
- [ ] Boutons assez grands (min 44px)

**Navigateurs:**
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (si disponible)

**Firebase:**
- [ ] Articles se chargent depuis Firestore
- [ ] Commande créée dans collection `commandes_en_ligne`
- [ ] Structure document conforme
- [ ] Pas d'erreur dans console Firebase

---

### Phase 7: Performance & SEO (20 min)

#### 7.1 Lighthouse (Chrome DevTools)
1. Ouvrir http://localhost:3000
2. F12 → Lighthouse
3. Sélectionner: Performance, Accessibility, Best Practices, SEO
4. Générer le rapport
5. **Objectif**: ≥ 90 sur toutes les catégories

#### 7.2 Optimisations si nécessaire

**Si Performance < 90:**
- Réduire taille des images
- Ajouter `priority` sur image hero
- Vérifier pas de dépendances lourdes

**Si SEO < 90:**
- Ajouter JSON-LD (Phase 3)
- Ajouter sitemap.xml (Phase 4)
- Vérifier toutes les meta tags

---

## 📋 RÉCAPITULATIF DES TÂCHES

### À faire AVANT déploiement (OBLIGATOIRE)
- [ ] **1.1** Installer @nuxtjs/pwa
- [ ] **1.2** Configurer PWA dans nuxt.config.ts
- [ ] **1.3** Ajouter icônes PWA (192x192, 512x512)
- [ ] **5.1** Configurer firestore.rules
- [ ] **5.2** Déployer règles Firestore
- [ ] **6.1** Tester flux complet
- [ ] **6.2** Tester responsive

### À faire APRÈS déploiement (AMÉLIORATIONS)
- [ ] **2.1-2.4** Ajouter tests automatisés (Vitest)
- [ ] **3.1-3.3** Implémenter JSON-LD
- [ ] **4.1-4.3** Générer sitemap.xml + robots.txt
- [ ] **7.1** Mesurer Lighthouse
- [ ] **7.2** Optimiser si nécessaire

---

## ⏱️ ESTIMATION TEMPS

| Phase | Durée | Priorité |
|-------|-------|----------|
| Phase 1: PWA | 30 min | 🔴 Haute |
| Phase 5: Règles Firestore | 15 min | 🔴 Haute |
| Phase 6: Tests manuels | 30 min | 🔴 Haute |
| Phase 7: Lighthouse | 20 min | 🟡 Moyenne |
| Phase 3: JSON-LD | 20 min | 🟡 Moyenne |
| Phase 4: Sitemap | 20 min | 🟡 Moyenne |
| Phase 2: Tests auto | 45 min | 🟢 Basse |

**Total pour 10/10**: ~2h30

**Minimum pour production**: ~1h15 (Phases 1, 5, 6)

---

## 🎯 CRITÈRES DE SUCCÈS 10/10

| Critère | Requis | Actuel | Après finalisation |
|---------|--------|--------|-------------------|
| Catalogue Firestore | ✅ | ✅ | ✅ |
| Fiches produits | ✅ | ✅ | ✅ |
| Panier fonctionnel | ✅ | ✅ | ✅ |
| Commandes Firestore | ✅ | ✅ | ✅ |
| **PWA installable** | ✅ | ⏳ | ✅ |
| **Lighthouse ≥ 90** | ✅ | ⏳ | ✅ |
| **SEO complet** | ✅ | ⏳ | ✅ |
| **Tests** | ✅ | ⏳ | ✅ |
| Documentation | ✅ | ✅ | ✅ |
| Build réussi | ✅ | ✅ | ✅ |

**Score final attendu: 10/10** 🎯

---

## 🚀 COMMANDES RAPIDES

```bash
# Développement
cd boutique
npm run dev

# Build
npm run build

# Tests (après installation Vitest)
npm run test

# Déploiement
firebase deploy --only hosting

# Générer sitemap (après configuration)
npm run generate:sitemap
```

---

## 📞 SUPPORT

En cas de problème:
1. Vérifier les logs Firebase Console
2. Vérifier la console navigateur (F12)
3. Consulter le README.md
4. Vérifier les règles Firestore

---

**Prêt à finaliser ?** 🚀

Commencez par la Phase 1 (PWA) pour avoir une application installable, puis la Phase 5 (règles Firestore) pour la sécurité, et enfin la Phase 6 (tests) pour valider le flux complet.