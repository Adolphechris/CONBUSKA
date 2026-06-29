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
            <li><NuxtLink :to="'/categorie/' + encodeURIComponent(produit?.categorie || '')" class="text-gray-500 hover:text-orange-600">{{ produit?.categorie }}</NuxtLink></li>
            <li class="text-gray-400">/</li>
            <li class="text-gray-800 font-semibold truncate max-w-xs">{{ produit?.nom }}</li>
          </ol>
        </nav>

        <div v-if="produit" class="grid md:grid-cols-2 gap-12">
          <!-- Galerie images -->
          <div class="space-y-4">
            <!-- Image principale -->
            <div class="bg-white rounded-2xl shadow-xl overflow-hidden">
              <img 
                :src="produit.image_url || '/images/default-product.jpg'" 
                :alt="produit.nom"
                class="w-full h-[500px] object-contain p-8"
              />
            </div>
            
            <!-- Miniatures (si plusieurs images) -->
            <div class="grid grid-cols-4 gap-4">
              <div class="bg-white rounded-lg shadow-md p-2 border-2 border-orange-500 cursor-pointer">
                <img 
                  :src="produit.image_url || '/images/default-product.jpg'" 
                  :alt="produit.nom"
                  class="w-full h-20 object-contain"
                />
              </div>
              <div class="bg-white rounded-lg shadow-md p-2 hover:border-2 hover:border-orange-500 cursor-pointer opacity-60">
                <div class="w-full h-20 bg-gray-100 rounded flex items-center justify-center text-gray-400">
                  +0
                </div>
              </div>
            </div>
          </div>

          <!-- Informations produit -->
          <div class="space-y-6">
            <!-- Badges -->
            <div class="flex flex-wrap gap-2">
              <span v-if="produit.nombre_ventes > 100" 
                    class="bg-red-500 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg">
                🔥 Best-seller
              </span>
              <span class="bg-orange-100 text-orange-700 px-4 py-2 rounded-full text-sm font-semibold">
                {{ produit.categorie }}
              </span>
              <span class="bg-green-100 text-green-700 px-4 py-2 rounded-full text-sm font-semibold">
                Garantie 2 ans
              </span>
            </div>

            <!-- Nom -->
            <h1 class="text-4xl font-bold text-gray-800 leading-tight">
              {{ produit.nom }}
            </h1>

            <!-- Référence -->
            <p class="text-gray-600">
              Réf: <span class="font-mono font-semibold">{{ produit.reference }}</span>
            </p>

            <!-- Prix -->
            <div class="bg-gradient-to-r from-orange-50 to-yellow-50 rounded-2xl p-6">
              <div class="flex items-baseline gap-3">
                <span class="text-5xl font-bold text-orange-600">
                  {{ formatPrix(produit.prix) }}
                </span>
                <span class="text-xl text-gray-600">{{ produit.devise }}</span>
              </div>
              <p class="text-sm text-gray-600 mt-2">
                Prix TTC. Livraison gratuite.
              </p>
            </div>

            <!-- Stock -->
            <div class="space-y-3">
              <div v-if="produit.stock_disponible > 10" 
                   class="flex items-center gap-3 text-green-700 bg-green-50 px-4 py-3 rounded-lg">
                <span class="w-3 h-3 bg-green-600 rounded-full animate-pulse"></span>
                <span class="font-semibold">En stock</span>
                <span class="text-sm">({{ produit.stock_disponible }} disponibles)</span>
              </div>
              <div v-else-if="produit.stock_disponible > 0" 
                   class="flex items-center gap-3 text-orange-700 bg-orange-50 px-4 py-3 rounded-lg">
                <span class="w-3 h-3 bg-orange-600 rounded-full animate-pulse"></span>
                <span class="font-semibold">Stock limité !</span>
                <span class="text-sm">Plus que {{ produit.stock_disponible }} en stock</span>
              </div>
              <div v-else 
                   class="flex items-center gap-3 text-red-700 bg-red-50 px-4 py-3 rounded-lg">
                <span class="w-3 h-3 bg-red-600 rounded-full"></span>
                <span class="font-semibold">Rupture de stock</span>
              </div>
            </div>

            <!-- Description -->
            <div v-if="produit.description" class="prose max-w-none">
              <h3 class="text-xl font-bold text-gray-800 mb-3">Description</h3>
              <p class="text-gray-700 leading-relaxed">{{ produit.description }}</p>
            </div>

            <!-- Caractéristiques -->
            <div class="bg-gray-50 rounded-xl p-6">
              <h3 class="text-xl font-bold text-gray-800 mb-4">Caractéristiques</h3>
              <div class="grid grid-cols-2 gap-4">
                <div class="flex items-center gap-2">
                  <span class="text-green-600">✓</span>
                  <span class="text-gray-700">Livraison gratuite RDC</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-green-600">✓</span>
                  <span class="text-gray-700">Garantie 2 ans</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-green-600">✓</span>
                  <span class="text-gray-700">Paiement à la livraison</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-green-600">✓</span>
                  <span class="text-gray-700">Retour sous 7 jours</span>
                </div>
              </div>
            </div>

            <!-- Quantité et ajout panier -->
            <div class="space-y-4">
              <div class="flex items-center gap-4">
                <label class="font-semibold text-gray-800">Quantité:</label>
                <div class="flex items-center border-2 border-gray-300 rounded-lg">
                  <button 
                    @click="quantite = Math.max(1, quantite - 1)"
                    class="px-4 py-2 hover:bg-gray-100 transition text-xl"
                  >−</button>
                  <input 
                    v-model="quantite"
                    type="number"
                    min="1"
                    :max="produit.stock_disponible"
                    class="w-20 text-center border-x-2 border-gray-300 py-2 focus:outline-none"
                  />
                  <button 
                    @click="quantite = Math.min(produit.stock_disponible, quantite + 1)"
                    class="px-4 py-2 hover:bg-gray-100 transition text-xl"
                  >+</button>
                </div>
              </div>

              <div class="flex gap-4">
                <button 
                  @click="ajouterAuPanier(produit, quantite)"
                  :disabled="produit.stock_disponible === 0"
                  class="flex-1 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed text-white font-bold py-4 px-8 rounded-xl transition transform hover:scale-105 shadow-xl text-lg"
                >
                  {{ produit.stock_disponible === 0 ? 'Rupture de stock' : '🛒 Ajouter au panier' }}
                </button>
                <button 
                  class="bg-white border-2 border-orange-500 text-orange-500 hover:bg-orange-50 font-bold py-4 px-6 rounded-xl transition"
                  title="Ajouter aux favoris"
                >
                  ♡
                </button>
              </div>

              <!-- Achat direct -->
              <button 
                v-if="produit.stock_disponible > 0"
                class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-8 rounded-xl transition"
              >
                ⚡ Achat express
              </button>
            </div>

            <!-- Trust badges -->
            <div class="grid grid-cols-3 gap-4 pt-6 border-t">
              <div class="text-center">
                <div class="text-2xl mb-2">🚚</div>
                <div class="text-xs text-gray-600">Livraison gratuite</div>
              </div>
              <div class="text-center">
                <div class="text-2xl mb-2">🛡️</div>
                <div class="text-xs text-gray-600">Garantie 2 ans</div>
              </div>
              <div class="text-center">
                <div class="text-2xl mb-2">↩️</div>
                <div class="text-xs text-gray-600">Retour 7 jours</div>
              </div>
            </div>
          </div>
        </div>

        <!-- État de chargement -->
        <div v-else class="text-center py-20">
          <div class="text-6xl mb-4 animate-spin">⏳</div>
          <p class="text-gray-600">Chargement du produit...</p>
        </div>

        <!-- Produits similaires -->
        <section v-if="produitsSimilaires.length > 0" class="mt-20">
          <h2 class="text-3xl font-bold text-gray-800 mb-8">
            Vous aimerez aussi
          </h2>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div 
              v-for="prod in produitsSimilaires" 
              :key="prod.code"
              class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition"
            >
              <NuxtLink :to="'/produit/' + prod.code">
                <img 
                  :src="prod.image_url || '/images/default-product.jpg'" 
                  :alt="prod.nom"
                  class="w-full h-48 object-cover"
                />
                <div class="p-4">
                  <h3 class="font-semibold text-gray-800 mb-2 line-clamp-2">{{ prod.nom }}</h3>
                  <div class="flex items-baseline gap-2">
                    <span class="text-xl font-bold text-orange-600">{{ formatPrix(prod.prix) }}</span>
                    <span class="text-sm text-gray-600">{{ prod.devise }}</span>
                  </div>
                </div>
              </NuxtLink>
            </div>
          </div>
        </section>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useHead } from '#app'

const route = useRoute()

// État
const produit = ref<any>(null)
const quantite = ref(1)
const produitsSimilaires = ref([])

// Meta tags dynamiques
useHead({
  title: () => produit.value ? `${produit.value.nom} - Ets La Lumière` : 'Produit - Ets La Lumière',
  meta: () => [
    { name: 'description', content: () => produit.value?.description?.substring(0, 160) || 'Découvrez ce produit d\'éclairage professionnel. Livraison gratuite, garantie 2 ans.' },
    { property: 'og:title', content: () => produit.value?.nom || 'Produit' },
    { property: 'og:description', content: () => produit.value?.description?.substring(0, 200) || '' },
    { property: 'og:type', content: 'website' }
  ]
})

// Charger le produit
onMounted(async () => {
  try {
    const { $firestore } = useNuxtApp()
    const code = route.params.code as string
    
    // Récupérer le produit
    const doc = await $firestore.getDocument('articles_publics', code)
    
    if (doc.exists) {
      produit.value = {
        code: doc.id,
        ...doc.data()
      }
      
      // Charger les produits similaires (même catégorie)
      const similairesSnapshot = await $firestore.getCollection('articles_publics', {
        where: [
          ['est_publie', '==', true],
          ['categorie', '==', produit.value.categorie]
        ],
        orderBy: ['nombre_ventes', 'desc'],
        limit: 4
      })
      
      produitsSimilaires.value = similairesSnapshot.docs
        .filter(d => d.id !== code)
        .map(d => ({
          code: d.id,
          ...d.data()
        }))
    } else {
      console.error('Produit non trouvé')
      // TODO: Rediriger vers 404
    }
    
  } catch (error) {
    console.error('Erreur chargement produit:', error)
  }
})

// Formatage prix
function formatPrix(prix: number) {
  return new Intl.NumberFormat('fr-FR').format(prix)
}

// Ajouter au panier
function ajouterAuPanier(produit: any, quantite: number) {
  const { $cart } = useNuxtApp()
  for (let i = 0; i < quantite; i++) {
    $cart.add(produit)
  }
}
</script>