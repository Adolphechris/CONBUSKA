<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    
    <main class="py-8">
      <div class="container mx-auto px-4">
        <!-- Breadcrumb -->
        <nav class="text-sm mb-6">
          <ol class="flex items-center space-x-2">
            <li><NuxtLink to="/" class="text-gray-500 hover:text-orange-600">Accueil</NuxtLink></li>
            <li class="text-gray-400">/</li>
            <li class="text-gray-800 font-semibold">{{ categorieNom }}</li>
          </ol>
        </nav>

        <!-- Header catégorie -->
        <div class="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 md:p-12 mb-8 text-white">
          <h1 class="text-4xl md:text-5xl font-bold mb-4">
            {{ categorieNom }}
          </h1>
          <p class="text-xl text-white/90 mb-6">
            {{ produits.length }} produits disponibles
          </p>
          
          <!-- Filtres -->
          <div class="flex flex-wrap gap-4">
            <select 
              v-model="triSelectionne"
              class="px-4 py-2 rounded-lg bg-white/20 backdrop-blur-sm text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-white"
            >
              <option value="popularite">Popularité</option>
              <option value="prix-asc">Prix croissant</option>
              <option value="prix-desc">Prix décroissant</option>
              <option value="nom">Nom A-Z</option>
              <option value="date">Nouveautés</option>
            </select>
            
            <select 
              v-model="filtrePrix"
              class="px-4 py-2 rounded-lg bg-white/20 backdrop-blur-sm text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-white"
            >
              <option value="">Tous les prix</option>
              <option value="0-10000">Moins de 10 000 FC</option>
              <option value="10000-50000">10 000 - 50 000 FC</option>
              <option value="50000-100000">50 000 - 100 000 FC</option>
              <option value="100000+">Plus de 100 000 FC</option>
            </select>
          </div>
        </div>

        <!-- Grille de produits -->
        <div v-if="produitsFiltres.length > 0" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          <div 
            v-for="produit in produitsFiltres" 
            :key="produit.code"
            class="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2 group"
          >
            <!-- Image avec overlay -->
            <div class="relative overflow-hidden">
              <img 
                :src="produit.image_url || '/images/default-product.jpg'" 
                :alt="produit.nom"
                class="w-full h-64 object-cover group-hover:scale-110 transition-transform duration-500"
                loading="lazy"
              />
              
              <!-- Badges -->
              <div class="absolute top-3 left-3 flex flex-col gap-2">
                <span v-if="produit.nombre_ventes > 100" 
                      class="bg-red-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg">
                  🔥 Best-seller
                </span>
                <span v-if="produit.stock_disponible <= 5 && produit.stock_disponible > 0" 
                      class="bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg">
                  Plus que {{ produit.stock_disponible }}!
                </span>
              </div>
              
              <!-- Quick actions overlay -->
              <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center gap-3">
                <NuxtLink 
                  :to="'/produit/' + produit.code"
                  class="bg-white text-gray-800 p-3 rounded-full hover:bg-orange-500 hover:text-white transition"
                  title="Voir détails"
                >
                  👁️
                </NuxtLink>
                <button 
                  @click="ajouterAuPanier(produit)"
                  :disabled="produit.stock_disponible === 0"
                  class="bg-orange-500 text-white p-3 rounded-full hover:bg-orange-600 disabled:bg-gray-400 transition"
                  title="Ajouter au panier"
                >
                  🛒
                </button>
              </div>
            </div>
            
            <!-- Contenu -->
            <div class="p-5">
              <div class="text-xs text-orange-600 font-semibold mb-2 uppercase tracking-wide">
                {{ produit.categorie }}
              </div>
              
              <h3 class="font-bold text-gray-800 mb-2 line-clamp-2 min-h-[56px] group-hover:text-orange-600 transition">
                {{ produit.nom }}
              </h3>
              
              <!-- Prix -->
              <div class="flex items-baseline gap-2 mb-4">
                <span class="text-3xl font-bold text-orange-600">
                  {{ formatPrix(produit.prix) }}
                </span>
                <span class="text-sm text-gray-600">{{ produit.devise }}</span>
              </div>
              
              <!-- Stock indicator -->
              <div class="mb-4">
                <div v-if="produit.stock_disponible > 10" 
                     class="flex items-center gap-2 text-green-600 text-sm">
                  <span class="w-2 h-2 bg-green-600 rounded-full"></span>
                  En stock
                </div>
                <div v-else-if="produit.stock_disponible > 0" 
                     class="flex items-center gap-2 text-orange-600 text-sm">
                  <span class="w-2 h-2 bg-orange-600 rounded-full animate-pulse"></span>
                  Stock limité ({{ produit.stock_disponible }})
                </div>
                <div v-else 
                     class="flex items-center gap-2 text-red-600 text-sm">
                  <span class="w-2 h-2 bg-red-600 rounded-full"></span>
                  Rupture de stock
                </div>
              </div>
              
              <!-- Bouton -->
              <button 
                @click="ajouterAuPanier(produit)"
                :disabled="produit.stock_disponible === 0"
                class="w-full bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition transform hover:scale-105 shadow-md"
              >
                {{ produit.stock_disponible === 0 ? 'Rupture de stock' : 'Ajouter au panier' }}
              </button>
            </div>
          </div>
        </div>

        <!-- État vide -->
        <div v-else class="text-center py-20">
          <div class="text-6xl mb-4">📦</div>
          <h3 class="text-2xl font-bold text-gray-800 mb-2">Aucun produit trouvé</h3>
          <p class="text-gray-600 mb-6">Essayez de modifier vos filtres</p>
          <NuxtLink 
            to="/categorie/tous" 
            class="inline-block bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 px-8 rounded-lg transition"
          >
            Voir tout le catalogue
          </NuxtLink>
        </div>

        <!-- Pagination (si nécessaire) -->
        <div v-if="produitsFiltres.length > 20" class="mt-12 flex justify-center gap-2">
          <button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50">
            ← Précédent
          </button>
          <button class="px-4 py-2 bg-orange-500 text-white rounded-lg">1</button>
          <button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">2</button>
          <button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">3</button>
          <button class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            Suivant →
          </button>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useHead } from '#app'

const route = useRoute()

// Meta tags
useHead({
  title: `${route.params.nom} - Ets La Lumière`,
  meta: [
    { name: 'description', content: `Découvrez notre gamme de ${route.params.nom}. Livraison gratuite, garantie 2 ans. +250 produits disponibles.` }
  ]
})

// État
const categorieNom = ref(decodeURIComponent(route.params.nom as string))
const produits = ref([])
const triSelectionne = ref('popularite')
const filtrePrix = ref('')

// Charger les produits
onMounted(async () => {
  try {
    const { $firestore } = useNuxtApp()
    
    let query = $firestore.getCollection('articles_publics', {
      where: [['est_publie', '==', true]],
      orderBy: ['nombre_ventes', 'desc']
    })
    
    const snapshot = await query
    const allProduits = snapshot.docs.map(doc => ({
      code: doc.id,
      ...doc.data()
    }))
    
    // Filtrer par catégorie
    if (categorieNom.value !== 'tous') {
      produits.value = allProduits.filter(p => 
        p.categorie.toLowerCase() === categorieNom.value.toLowerCase()
      )
    } else {
      produits.value = allProduits
    }
    
  } catch (error) {
    console.error('Erreur chargement catégorie:', error)
  }
})

// Filtres et tri
const produitsFiltres = computed(() => {
  let result = [...produits.value]
  
  // Filtre prix
  if (filtrePrix.value) {
    const [min, max] = filtrePrix.value.split('-').map(v => v ? parseInt(v) : Infinity)
    result = result.filter(p => {
      if (max === Infinity) return p.prix >= min
      return p.prix >= min && p.prix <= max
    })
  }
  
  // Tri
  switch (triSelectionne.value) {
    case 'prix-asc':
      result.sort((a, b) => a.prix - b.prix)
      break
    case 'prix-desc':
      result.sort((a, b) => b.prix - a.prix)
      break
    case 'nom':
      result.sort((a, b) => a.nom.localeCompare(b.nom))
      break
    case 'date':
      result.sort((a, b) => new Date(b.date_mise_a_jour).getTime() - new Date(a.date_mise_a_jour).getTime())
      break
    case 'popularite':
    default:
      result.sort((a, b) => (b.nombre_ventes || 0) - (a.nombre_ventes || 0))
  }
  
  return result
})

// Formatage prix
function formatPrix(prix: number) {
  return new Intl.NumberFormat('fr-FR').format(prix)
}

// Ajouter au panier
function ajouterAuPanier(produit: any) {
  const { $cart } = useNuxtApp()
  $cart.add(produit)
}
</script>