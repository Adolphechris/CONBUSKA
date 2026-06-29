# 🎯 Guide du Site - Ets La Lumière

**Version**: 1.0  
**Date**: 27 Juin 2026

---

## 📋 Structure des pages

| URL | Page | Description |
|-----|------|-------------|
| `/` | Accueil | Hero, catégories, nouveautés, vedettes, témoignages, newsletter |
| `/categorie/{slug}` | Catégorie | Produits filtrés par catégorie |
| `/produit/{code}` | Fiche produit | Galerie, description, prix, ajout panier |
| `/recherche?q=` | Recherche | Résultats de recherche |
| `/panier` | Panier | Lignes produits, résumé, commande |
| `/checkout` | Commande | Formulaire client, validation |
| `/confirmation` | Confirmation | Détail commande, suivi |
| `/a-propos` | À propos | Histoire, valeurs, équipe |
| `/contact` | Contact | Formulaire, adresse, carte |
| `/livraison` | Livraison | Zones, délais, retours |
| `/faq` | FAQ | Questions fréquentes |
| `/mentions-legales` | Mentions légales | Informations légales |
| `/politique-confidentialite` | Confidentialité | Politique de données |

---

## 🎨 Charte graphique

### Couleurs
```css
/* Primaire (orange) */
--color-primary: #F97316;
--color-primary-hover: #EA580C;

/* Secondaire (vert) */
--color-secondary: #10B981;
--color-secondary-hover: #059669;

/* Accent (or) */
--color-accent: #F59E0B;

/* Foncé */
--color-dark: #1F2937;
--color-darker: #111827;

/* Clair */
--color-light: #F9FAFB;
--color-white: #FFFFFF;

/* Texte */
--color-text: #1F2937;
--color-text-muted: #6B7280;
--color-text-light: #FFFFFF;

/* Bordures */
--border-color: #D1D5DB;
--border-radius: 0.5rem;
--border-radius-lg: 1rem;
--border-radius-full: 9999px;
```

### Typographie
```css
font-family: 'Inter', sans-serif;
font-weight: 400 (regular), 600 (semibold), 700 (bold), 800 (extrabold)
```

### Boutons
```css
/* Principal */
.btn-primary {
  background: #F97316;
  color: white;
  border-radius: 9999px;
  padding: 0.75rem 2rem;
  box-shadow: 0 4px 6px rgba(249, 115, 22, 0.3);
}

/* Secondaire */
.btn-secondary {
  background: white;
  border: 2px solid #F97316;
  color: #F97316;
  border-radius: 9999px;
  padding: 0.75rem 2rem;
}

/* Désactivé */
.btn-disabled {
  background: #D1D5DB;
  color: #9CA3AF;
  border-radius: 9999px;
  padding: 0.75rem 2rem;
}
```

### Animations
```css
/* Zoom image */
.product-card img {
  transition: transform 0.3s ease;
}
.product-card:hover img {
  transform: scale(1.05);
}

/* Shadow */
.product-card {
  transition: box-shadow 0.3s ease, transform 0.3s ease;
}
.product-card:hover {
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  transform: translateY(-5px);
}

/* Fade-in */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
```

---

## 📝 Comment modifier le contenu statique

### Pages avec contenu intégré
- `a-propos.vue` - Texte dans le template
- `livraison.vue` - Zones, délais, politique retour
- `faq.vue` - Questions/réponses dans `faqItems`
- `mentions-legales.vue` - Texte dans le template

**Pour modifier**: Ouvrir le fichier `.vue`, chercher le texte à modifier dans la section `<template>`, le remplacer, et redéployer.

### Pages avec Firestore
- `contact.vue` - Les messages sont sauvegardés dans `contact_messages`
- `index.vue` (newsletter) - Les emails sont sauvegardés dans `newsletter_subscribers`

**Pour consulter les données**: Se connecter à Firebase Console → Firestore Database → Collection concernée.

---

## 🎪 Comment activer/désactiver les promotions

1. Aller sur **Firebase Console** → Firestore Database
2. Créer une collection `promotions`
3. Ajouter un document avec les champs:
   ```json
   {
     "actif": true,
     "texte": "Soldes d'été - 10% sur tout",
     "couleur_fond": "#F97316",
     "couleur_texte": "#FFFFFF",
     "date_debut": "2026-07-01",
     "date_fin": "2026-07-31"
   }
   ```
4. Pour désactiver: mettre `actif: false` ou supprimer le document

---

## 🖼️ Comment changer le logo

1. Créer une image PNG/SVG (idéalement 200x50px)
2. Placer le fichier dans `boutique/public/logo.png`
3. Modifier `components/AppLogo.vue`:
   ```vue
   <NuxtLink to="/" class="logo">
     <img src="/logo.png" alt="Ets La Lumière" width="180" height="45" />
   </NuxtLink>
   ```
4. Redéployer

Si aucune image, le logo textuel s'affiche automatiquement avec la police Inter et la couleur orange.

---

## 🚀 Procédure de déploiement

### Prérequis
```bash
# Firebase CLI
npm install -g firebase-tools

# Se connecter
firebase login
```

### Build et déploiement
```bash
cd boutique

# Build complet
npm run build

# Générer le site statique
npm run generate

# Déployer sur Firebase
firebase deploy --only hosting

# Ou déployer tout (hosting + firestore + storage)
firebase deploy
```

### Vérifier le déploiement
```bash
# URL de production
https://projet-id.web.app

# Vérifier les pages
https://projet-id.web.app/a-propos
https://projet-id.web.app/contact
https://projet-id.web.app/faq
```

---

## 🔧 Technologies utilisées

- **Framework**: Nuxt.js 3
- **CSS**: Framework CSS personnalisé (variables CSS, scoped styles)
- **Base de données**: Firebase Firestore
- **Hébergement**: Firebase Hosting
- **Images**: Firebase Storage
- **PWA**: Service Worker, Manifest, Offline support

---

## 📈 SEO

### Données structurées
- `Organization` sur l'accueil
- `Product` sur chaque fiche produit
- `BreadcrumbList` sur les pages internes
- `FAQPage` sur la page FAQ

### Meta tags
- Titre unique par page
- Meta description
- Open Graph (Facebook)
- Twitter Cards

### Fichiers
- `/sitemap.xml` généré dynamiquement
- `/robots.txt` configuré

---

**Guide mis à jour le**: 27 Juin 2026  
**Documentation**: `SITE_GUIDE.md`