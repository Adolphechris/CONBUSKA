#!/usr/bin/env node

/**
 * Script de génération du sitemap.xml
 * Récupère tous les articles depuis Firestore et génère le sitemap
 */

import { initializeApp } from 'firebase/app'
import { getFirestore, collection, getDocs } from 'firebase/firestore'
import { writeFileSync } from 'fs'
import { join } from 'path'

// Configuration Firebase depuis les variables d'environnement
const firebaseConfig = {
  apiKey: process.env.VITE_FIREBASE_API_KEY,
  authDomain: process.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: process.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.VITE_FIREBASE_APP_ID
}

const baseUrl = 'https://boutique.conbuska.cd'

async function generateSitemap() {
  console.log('🔄 Génération du sitemap...')
  
  // Initialiser Firebase
  const app = initializeApp(firebaseConfig)
  const db = getFirestore(app)
  
  let urls = []
  
  try {
    // Pages statiques
    urls.push({
      loc: `${baseUrl}/`,
      changefreq: 'daily',
      priority: '1.0'
    })
    
    urls.push({
      loc: `${baseUrl}/panier`,
      changefreq: 'weekly',
      priority: '0.5'
    })
    
    urls.push({
      loc: `${baseUrl}/checkout`,
      changefreq: 'weekly',
      priority: '0.5'
    })
    
    // Récupérer tous les articles depuis Firestore
    console.log('📦 Récupération des articles depuis Firestore...')
    const articlesRef = collection(db, 'articles_publics')
    const snapshot = await getDocs(articlesRef)
    
    // Ajouter chaque article
    snapshot.docs.forEach(doc => {
      const data = doc.data()
      urls.push({
        loc: `${baseUrl}/produit/${doc.id}`,
        lastmod: data.date_mise_a_jour?.toDate().toISOString() || new Date().toISOString(),
        changefreq: 'weekly',
        priority: '0.8'
      })
    })
    
    console.log(`✅ ${snapshot.size} articles trouvés`)
    
    // Récupérer les catégories (depuis les articles uniques)
    const categories = new Set(snapshot.docs.map(doc => doc.data().categorie).filter(Boolean))
    categories.forEach(categorie => {
      const encodedCategorie = encodeURIComponent(categorie)
      urls.push({
        loc: `${baseUrl}/categorie/${encodedCategorie}`,
        changefreq: 'daily',
        priority: '0.9'
      })
    })
    
    console.log(`✅ ${categories.size} catégories trouvées`)
    
    // Générer le XML
    const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map(url => `  <url>
    <loc>${url.loc}</loc>
    ${url.lastmod ? `<lastmod>${url.lastmod}</lastmod>` : ''}
    <changefreq>${url.changefreq}</changefreq>
    <priority>${url.priority}</priority>
  </url>`).join('\n')}
</urlset>`
    
    // Écrire le fichier
    const outputPath = join(process.cwd(), 'public', 'sitemap.xml')
    writeFileSync(outputPath, sitemap, 'utf-8')
    
    console.log(`✅ Sitemap généré avec succès!`)
    console.log(`   📄 Fichier: ${outputPath}`)
    console.log(`   📊 URLs: ${urls.length}`)
    console.log(`   🕐 Date: ${new Date().toISOString()}`)
    
  } catch (error) {
    console.error('❌ Erreur lors de la génération du sitemap:', error)
    process.exit(1)
  }
}

// Exécuter
generateSitemap().catch(console.error)