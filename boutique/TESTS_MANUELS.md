# 🧪 GUIDE DE TESTS MANUELS - Sprint 3

**Objectif**: Valider toutes les fonctionnalités avant déploiement  
**Durée estimée**: 30 minutes  
**Statut**: À compléter

---

## 📋 PRÉREQUIS

- [ ] Application lancée: `npm run dev` → http://localhost:3000
- [ ] Firebase configuré avec clés valides
- [ ] Collection `articles_publics` peuplée avec des produits de test
- [ ] Navigateur Chrome/Firefox ouvert

---

## ✅ TESTS FONCTIONNELS

### 1. Page d'accueil (`/`)

**Test 1.1: Affichage général**
- [ ] La page se charge sans erreur
- [ ] Le header s'affiche avec logo, recherche, icône panier
- [ ] Le footer s'affiche avec contact et liens
- [ ] La section hero est visible
- [ ] Les produits vedettes s'affichent (max 8)
- [ ] Les catégories s'affichent

**Test 1.2: Navigation**
- [ ] Clic sur logo → retour à l'accueil
- [ ] Clic sur une catégorie → redirection vers `/categorie/{nom}`
- [ ] Clic sur recherche → focus dans la barre de recherche
- [ ] Clic sur icône panier → redirection vers `/panier`

**Test 1.3: Recherche**
- [ ] Saisir "test" dans la barre de recherche
- [ ] Appuyer sur Entrée
- [ ] Vérifier redirection vers `/recherche?q=test`
- [ ] Vérifier affichage des résultats
- [ ] Vérifier message "Aucun produit trouvé" si pas de résultat

---

### 2. Page Catégorie (`/categorie/{nom}`)

**Test 2.1: Affichage**
- [ ] Titre de la catégorie s'affiche
- [ ] Grille de produits s'affiche (24 produits max par page)
- [ ] Pagination s'affiche si > 24 produits
- [ ] Badges stock visibles (vert/orange/rouge)

**Test 2.2: Pagination**
- [ ] Cliquer sur page 2 → URL change, produits défilent
- [ ] Cliquer sur "Précédent" → retour page 1
- [ ] Vérifier qu'il n'y a pas de doublons entre pages

**Test 2.3: Filtres (si implémentés)**
- [ ] Trier par prix croissant
- [ ] Trier par date

---

### 3. Page Produit (`/produit/{code}`)

**Test 3.1: Affichage produit**
- [ ] Image du produit s'affiche (ou image par défaut)
- [ ] Nom du produit en h1
- [ ] Catégorie affichée
- [ ] Prix formaté (ex: "10 000 CDF")
- [ ] Badge stock visible et correct (vert/orange/rouge)
- [ ] Description affichée si existe
- [ ] Bouton "Ajouter au panier" visible

**Test 3.2: Bouton Ajouter**
- [ ] Si stock > 0: bouton actif, texte "Ajouter au panier"
- [ ] Si stock = 0: bouton désactivé, texte "Rupture de stock"
- [ ] Clic sur bouton → alert "Produit ajouté au panier!"
- [ ] Vérifier que le panier se met à jour (icône)

**Test 3.3: SEO**
- [ ] Titre de la page: `{nom} - Ets La Lumière`
- [ ] Meta description présente
- [ ] URL canonique correcte
- [ ] Open Graph tags présents (inspecter le HTML)

---

### 4. Panier (`/panier`)

**Test 4.1: Affichage panier vide**
- [ ] Message "Votre panier est vide" s'affiche
- [ ] Bouton "Retour à l'accueil" visible
- [ ] Total = 0

**Test 4.2: Ajout d'articles**
- [ ] Depuis page produit, ajouter 2 articles différents
- [ ] Aller sur `/panier`
- [ ] Vérifier que les 2 articles sont présents
- [ ] Vérifier les quantités (1 par défaut)
- [ ] Vérifier les prix
- [ ] Vérifier le total

**Test 4.3: Modification quantités**
- [ ] Cliquer sur "+" → quantité augmente, total augmente
- [ ] Cliquer sur "-" → quantité diminue, total diminue
- [ ] Si quantité = 1 et clic sur "-" → article supprimé (ou confirmation)
- [ ] Vérifier que le total se met à jour en temps réel

**Test 4.4: Suppression**
- [ ] Cliquer sur icône corbeille
- [ ] Article disparaît du panier
- [ ] Total se met à jour
- [ ] Si panier vide → message "panier vide"

**Test 4.5: Persistance**
- [ ] Ajouter un article
- [ ] Recharger la page (F5)
- [ ] Article toujours présent dans le panier
- [ ] Fermer le navigateur
- [ ] Rouvrir et aller sur `/panier`
- [ ] Article toujours présent

**Test 4.6: Continuer vers checkout**
- [ ] Cliquer sur "Passer la commande"
- [ ] Redirection vers `/checkout`

---

### 5. Checkout (`/checkout`)

**Test 5.1: Affichage formulaire**
- [ ] Récapitulatif du panier visible
- [ ] Formulaire avec champs: Nom, Email, Téléphone, Adresse
- [ ] Champ "Nom" marqué comme obligatoire
- [ ] Champ "Email" marqué comme obligatoire
- [ ] Bouton "Confirmer la commande" visible

**Test 5.2: Validation**
- [ ] Laisser champs vides, cliquer "Confirmer"
- [ ] Vérifier message d'erreur pour nom
- [ ] Vérifier message d'erreur pour email
- [ ] Saisir email invalide (ex: "test")
- [ ] Vérifier message d'erreur email

**Test 5.3: Soumission**
- [ ] Remplir formulaire avec données valides:
  - Nom: "Jean Dupont"
  - Email: "jean@example.com"
  - Téléphone: "+242 06 123 4567"
  - Adresse: "123 Rue Test, Kinshasa"
- [ ] Cliquer "Confirmer la commande"
- [ ] Vérifier redirection vers `/confirmation`
- [ ] Vérifier affichage ID de commande
- [ ] Vérifier message de succès

**Test 5.4: Vérification Firebase**
- [ ] Ouvrir Firebase Console
- [ ] Aller dans Firestore > `commandes_en_ligne`
- [ ] Vérifier qu'une nouvelle commande a été créée
- [ ] Vérifier la structure du document:
  - `date_commande`: timestamp
  - `client.nom`: "Jean Dupont"
  - `client.email`: "jean@example.com"
  - `client.telephone`: "+242 06 123 4567"
  - `client.adresse`: "123 Rue Test, Kinshasa"
  - `lignes`: array avec articles
  - `total`: nombre
  - `statut`: "nouveau"

**Test 5.5: Panier vidé**
- [ ] Retourner sur `/panier`
- [ ] Vérifier que le panier est vide

---

### 6. Confirmation (`/confirmation`)

**Test 6.1: Affichage**
- [ ] Message de confirmation visible
- [ ] ID de commande affiché
- [ ] Récapitulatif de la commande visible
- [ ] Bouton "Retour à l'accueil" visible
- [ ] Bouton "Voir mes commandes" (si implémenté)

**Test 6.2: Navigation**
- [ ] Clic "Retour à l'accueil" → retour sur `/`
- [ ] Le panier reste vide

---

### 7. Recherche (`/recherche?q={query}`)

**Test 7.1: Recherche avec résultats**
- [ ] Aller sur `/recherche?q=test`
- [ ] Vérifier titre: `Résultats de recherche: "test"`
- [ ] Vérifier affichage des produits correspondants
- [ ] Vérifier que la recherche est insensible à la casse

**Test 7.2: Recherche sans résultat**
- [ ] Aller sur `/recherche?q=xyznonexistant`
- [ ] Vérifier message "Aucun produit trouvé"
- [ ] Vérifier bouton "Retour à l'accueil"

**Test 7.3: Recherche par catégorie**
- [ ] Aller sur `/recherche?q=électronique` (nom de catégorie)
- [ ] Vérifier que les produits de cette catégorie s'affichent

---

## 📱 TESTS RESPONSIVE

### Mobile (375px - iPhone SE)
- [ ] Header: logo + icônes bien espacés
- [ ] Grille produits: 1 colonne
- [ ] Fiche produit: image au-dessus, infos en dessous
- [ ] Panier: liste verticale
- [ ] Checkout: formulaire en colonne
- [ ] Boutons assez grands (min 44px)
- [ ] Texte lisible (min 14px)

### Tablette (768px - iPad)
- [ ] Grille produits: 2-3 colonnes
- [ ] Fiche produit: côte à côte (image + infos)
- [ ] Navigation tactile OK

### Desktop (1024px+)
- [ ] Grille produits: 4 colonnes
- [ ] Header: tous les éléments visibles
- [ ] Footer: colonnes alignées
- [ ] Contenu centré (max-width: 1280px)

---

## 🌐 TESTS NAVIGATEURS

### Chrome/Edge (Chromium)
- [ ] Toutes les fonctionnalités marchent
- [ ] PWA: vérifier icône dans la barre d'adresse
- [ ] Console: pas d'erreur

### Firefox
- [ ] Toutes les fonctionnalités marchent
- [ ] Layout correct
- [ ] Console: pas d'erreur

### Safari (si disponible)
- [ ] Toutes les fonctionnalités marchent
- [ ] Layout correct
- [ ] Console: pas d'erreur

---

## 🔥 TESTS FIREBASE

### Firestore - articles_publics
- [ ] Les articles se chargent correctement
- [ ] Pas d'erreur de permission dans console
- [ ] Images s'affichent (Firebase Storage)

### Firestore - commandes_en_ligne
- [ ] Nouvelle commande créée après checkout
- [ ] Structure du document conforme
- [ ] Pas de champ en trop
- [ ] Pas de champ manquant
- [ ] Timestamp présent

### Règles Firestore
- [ ] Impossible de lire les commandes (sans auth)
- [ ] Impossible de modifier/supprimer articles
- [ ] Impossible de créer commande sans champs requis

---

## ♿ TESTS ACCESSIBILITÉ

- [ ] Contraste texte/background suffisant (WCAG AA)
- [ ] Navigation au clavier possible (Tab, Entrée)
- [ ] Focus visible sur éléments interactifs
- [ ] Alt text sur toutes les images
- [ ] Labels sur tous les inputs
- [ ] Ordre de tabulation logique

---

## ⚡ TESTS PERFORMANCE

### Lighthouse (Chrome DevTools)
1. Ouvrir http://localhost:3000
2. F12 → Lighthouse
3. Sélectionner: Performance, Accessibility, Best Practices, SEO
4. Générer le rapport

**Objectifs:**
- [ ] Performance: ≥ 90
- [ ] Accessibility: ≥ 90
- [ ] Best Practices: ≥ 90
- [ ] SEO: ≥ 90

### Vérifications manuelles
- [ ] Page d'accueil charge en < 3s
- [ ] Images se chargent progressivement (lazy loading)
- [ ] Pas de scrollbar horizontale
- [ ] Animations fluides (60fps)

---

## 🐛 TESTS ERREURS

### Cas d'erreur à tester
- [ ] Produit inexistant: `/produit/INVALID` → message "Produit non trouvé"
- [ ] Catégorie vide: `/categorie/inexistante` → message "Aucun produit"
- [ ] Firebase déconnecté: message d'erreur approprié
- [ ] localStorage désactivé: panier ne fonctionne pas (fallback)

---

## 📊 RÉSULTATS

### Tests réussis: ___ / ___

### Bugs trouvés:
1. 
2. 
3. 

### Notes:
- 

---

## ✅ SIGNATURE

**Testé par**: _________________  
**Date**: _________________  
**Résultat**: ☐ PASS  ☐ FAIL

**Actions à corriger (si FAIL):**
1. 
2. 
3. 

**Re-test après correction**: ☐ PASS  ☐ FAIL  
**Date re-test**: _________________