<template>
  <div class="min-h-screen bg-white">
    <AppHeader />
    
    <!-- Hero Section Premium -->
    <section class="relative h-[600px] md:h-[700px] overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-r from-orange-600 via-orange-500 to-yellow-500">
        <!-- Animation de fond -->
        <div class="absolute inset-0 opacity-20">
          <div class="absolute top-10 left-10 w-32 h-32 bg-white rounded-full blur-3xl animate-pulse"></div>
          <div class="absolute bottom-20 right-20 w-48 h-48 bg-yellow-300 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s"></div>
          <div class="absolute top-1/2 left-1/3 w-40 h-40 bg-orange-300 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s"></div>
        </div>
      </div>
      
      <div class="relative container mx-auto px-4 h-full flex items-center">
        <div class="grid md:grid-cols-2 gap-12 items-center w-full">
          <!-- Texte Hero -->
          <div class="text-white space-y-6">
            <div class="inline-block bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-semibold mb-4">
              🏆 Leader de l'éclairage en RDC depuis 2010
            </div>
            
            <h1 class="text-5xl md:text-7xl font-bold leading-tight">
              Tout l'univers de
              <span class="text-yellow-300">Ets La Lumière</span>
            </h1>
            
            <p class="text-xl md:text-2xl text-white/90 leading-relaxed">
              Découvrez +10 000 produits d'éclairage professionnel. 
              Livraison gratuite partout en RDC. Paiement à la livraison.
            </p>
            
            <div class="flex flex-wrap gap-4 pt-4">
              <NuxtLink 
                to="/categorie/tous" 
                class="bg-white text-orange-600 px-8 py-4 rounded-full font-bold text-lg hover:bg-yellow-50 transition transform hover:scale-105 shadow-2xl"
              >
                Découvrir le catalogue
              </NuxtLink>
              <a 
                href="tel:+243812345678" 
                class="bg-transparent border-2 border-white text-white px-8 py-4 rounded-full font-bold text-lg hover:bg-white/10 transition"
              >
                📞 +243 81 234 56 78
              </a>
            </div>
            
            <!-- Trust badges -->
            <div class="flex flex-wrap gap-6 pt-8 text-white/90 text-sm">
              <div class="flex items-center gap-2">
                <span class="text-2xl">✓</span>
                <span>Garantie 2 ans</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-2xl">✓</span>
                <span>Livraison gratuite</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-2xl">✓</span>
                <span>Paiement sécurisé</span>
              </div>
            </div>
          </div>
          
          <!-- Image Hero -->
          <div class="hidden md:block">
            <div class="relative">
              <div class="absolute -inset-4 bg-white/20 rounded-full blur-2xl"></div>
              <img 
                src="/images/hero-product.png" 
                alt="Produits d'éclairage Ets La Lumière"
                class="relative w-full h-[500px] object-contain drop-shadow-2xl"
                onerror="this.style.display='none'"
              />
              <!-- Fallback si pas d'image -->
              <div v-if="!heroImageLoaded" class="relative bg-white/10 backdrop-blur-sm rounded-3xl p-12 text-center">
                <div class="text-9xl mb-4">💡</div>
                <p class="text-white text-xl font-semibold">Éclairage Professionnel</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Vague en bas -->
      <div class="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="white"/>
        </svg>
      </div>
    </section>

    <!-- Barre de confiance -->
    <section class="bg-gray-50 py-8 border-b">
      <div class="container mx-auto px-4">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div class="flex items-center justify-center gap-3">
            <div class="text-3xl">🚚</div>
            <div>
              <div class="font-bold text-gray-800">Livraison Gratuite</div>
              <div class="text-sm text-gray-600">Partout en RDC</div>
            </div>
          </div>
          <div class="flex items-center justify-center gap-3">
            <div class="text-3xl">💳</div>
            <div>
              <div class="font-bold text-gray-800">Paiement à la Livraison</div>
              <div class="text-sm text-gray-600">100% sécurisé</div>
            </div>
          </div>
          <div class="flex items-center justify-center gap-3">
            <div class="text-3xl">🛡️</div>
            <div>
              <div class="font-bold text-gray-800">Garantie 2 Ans</div>
              <div class="text-sm text-gray-600">Sur tous les produits</div>
            </div>
          </div>
          <div class="flex items-center justify-center gap-3">
            <div class="text-3xl">⭐</div>
            <div>
              <div class="font-bold text-gray-800">15+ Ans d'Expérience</div>
              <div class="text-sm text-gray-600">Leader du marché</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Catégories populaires -->
    <section class="py-16 bg-white">
      <div class="container mx-auto px-4">
        <div class="text-center mb-12">
          <h2 class="text-4xl font-bold text-gray-800 mb-4">
            Catégories Populaires
          </h2>
          <p class="text-gray-600 text-lg max-w-2xl mx-auto">
            Explorez notre large gamme de produits d'éclairage professionnel
          </p>
        </div>
        
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          <NuxtLink 
            v-for="categorie in categories" 
            :key="categorie.nom"
            :to="'/categorie/' + encodeURIComponent(categorie.nom)"
            class="group bg-gradient-to-br from-orange-50 to-yellow-50 rounded-2xl p-6 text-center hover:shadow-2xl transition transform hover:-translate-y-2"
          >
            <div class="text-5xl mb-4 group-hover:scale-110 transition-transform">
              {{ categorie.icone }}
            </div>
            <h3 class="font-bold text-gray-800 group-hover:text-orange-600 transition">
              {{ categorie.nom }}
            </h3>
            <p class="text-sm text-gray-600 mt-1">
              {{ categorie.nombre }} produits
            </p>
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- Produits vedettes (Meilleures ventes) -->
    <section class="py-16 bg-gray-50">
      <div class="container mx-auto px-4">
        <div class="flex justify-between items-center mb-12">
          <div>
            <h2 class="text-4xl font-bold text-gray-800 mb-2">
              🔥 Nos Meilleures Ventes
            </h2>
            <p class="text-gray-600 text-lg">
              Les produits préférés de nos clients
            </p>
          </div>
          <NuxtLink 
            to="/categorie/tous" 
            class="hidden md:inline-flex items-center gap-2 text-orange-600 font-semibold hover:text-orange-700 transition"
          >
            Voir tout le catalogue
            <span class="text-xl">→</span>
          </NuxtLink>
        </div>
        
        <!-- Carrousel horizontal sur mobile, grille sur desktop -->
        <div class="relative">
          <div class="flex gap-6 overflow-x-auto pb-4 md:grid md:grid-cols-4 md:overflow-visible snap-x snap-mandatory scrollbar-hide">
            <div 
              v-for="produit in produitsVedettes" 
              :key="produit.code"
              class="min-w-[280px] md:min-w-0 bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition transform hover:-translate-y-1 snap-start"
            >
              <div class="relative">
                <img 
                  :src="produit.image_url || '/images/default-product.jpg'" 
                  :alt="produit.nom"
                  class="w-full h-64 object-cover"
                  loading="lazy"
                />
                <div v-if="produit.stock_disponible <= 5 && produit.stock_disponible > 0" 
                     class="absolute top-4 right-4 bg-orange-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                  Plus que {{ produit.stock_disponible }}!
                </div>
                <div v-if="produit.stock_disponible === 0" 
                     class="absolute top-4 right-4 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                  Rupture
                </div>
              </div>
              
              <div class="p-5">
                <div class="text-xs text-gray-500 mb-2">{{ produit.categorie }}</div>
                <h3 class="font-bold text-gray-800 mb-2 line-clamp-2 min-h-[48px]">
                  {{ produit.nom }}
                </h3>
                
                <div class="flex items-baseline gap-2 mb-4">
                  <span class="text-2xl font-bold text-orange-600">
                    {{ formatPrix(produit.prix) }}
                  </span>
                  <span class="text-sm text-gray-600">{{ produit.devise }}</span>
                </div>
                
                <button 
                  @click="ajouterAuPanier(produit)"
                  :disabled="produit.stock_disponible === 0"
                  class="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition"
                >
                  {{ produit.stock_disponible === 0 ? 'Rupture de stock' : 'Ajouter au panier' }}
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="text-center mt-8 md:hidden">
          <NuxtLink 
            to="/categorie/tous" 
            class="inline-flex items-center gap-2 text-orange-600 font-semibold"
          >
            Voir tout le catalogue
            <span class="text-xl">→</span>
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- Bannière promotionnelle -->
    <section class="py-16 bg-gradient-to-r from-purple-600 to-pink-600 text-white">
      <div class="container mx-auto px-4">
        <div class="max-w-4xl mx-auto text-center space-y-6">
          <div class="text-6xl mb-4">🎉</div>
          <h2 class="text-4xl md:text-5xl font-bold">
            Offre Spéciale - Nouveaux Clients
          </h2>
          <p class="text-xl text-white/90">
            -10% sur votre première commande avec le code :
            <span class="bg-white text-purple-600 px-4 py-2 rounded-lg font-bold text-2xl inline-block mt-2">
              BIENVENUE10
            </span>
          </p>
          <p class="text-white/80">
            Valable sur tout le catalogue. Cumulable avec la livraison gratuite.
          </p>
        </div>
      </div>
    </section>

    <!-- Nouveautés -->
    <section class="py-16 bg-white">
      <div class="container mx-auto px-4">
        <div class="text-center mb-12">
          <h2 class="text-4xl font-bold text-gray-800 mb-4">
            ✨ Tout Juste Arrivé
          </h2>
          <p class="text-gray-600 text-lg">
            Les dernières nouveautés de notre catalogue
          </p>
        </div>
        
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div 
            v-for="produit in nouveautes" 
            :key="produit.code"
            class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition"
          >
            <img 
              :src="produit.image_url || '/images/default-product.jpg'" 
              :alt="produit.nom"
              class="w-full h-48 object-cover"
              loading="lazy"
            />
            <div class="p-4">
              <h3 class="font-semibold text-gray-800 mb-2 line-clamp-2">
                {{ produit.nom }}
              </h3>
              <div class="flex items-baseline gap-2">
                <span class="text-xl font-bold text-orange-600">
                  {{ formatPrix(produit.prix) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Témoignages -->
    <section class="py-16 bg-gray-50">
      <div class="container mx-auto px-4">
        <div class="text-center mb-12">
          <h2 class="text-4xl font-bold text-gray-800 mb-4">
            Ce que disent nos clients
          </h2>
          <p class="text-gray-600 text-lg">
            Plus de 5 000 clients nous font confiance
          </p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div class="bg-white rounded-2xl shadow-lg p-8">
            <div class="flex items-center gap-1 mb-4">
              <span v-for="i in 5" :key="i" class="text-yellow-400 text-xl">⭐</span>
            </div>
            <p class="text-gray-700 mb-6 italic">
              "Service exceptionnel ! Livraison rapide à Kinshasa. Les produits sont de très haute qualité. Je recommande vivement Ets La Lumière."
            </p>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center text-2xl">
                👨‍💼
              </div>
              <div>
                <div class="font-bold text-gray-800">Jean-Pierre M.</div>
                <div class="text-sm text-gray-600">Kinshasa, RDC</div>
              </div>
            </div>
          </div>
          
          <div class="bg-white rounded-2xl shadow-lg p-8">
            <div class="flex items-center gap-1 mb-4">
              <span v-for="i in 5" :key="i" class="text-yellow-400 text-xl">⭐</span>
            </div>
            <p class="text-gray-700 mb-6 italic">
              "Prix imbattables et équipe professionnelle. J'ai équipé tout mon bureau avec leurs produits. Le service après-vente est impeccable."
            </p>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center text-2xl">
                👩‍💼
              </div>
              <div>
                <div class="font-bold text-gray-800">Marie-Claire K.</div>
                <div class="text-sm text-gray-600">Lubumbashi, RDC</div>
              </div>
            </div>
          </div>
          
          <div class="bg-white rounded-2xl shadow-lg p-8">
            <div class="flex items-center gap-1 mb-4">
              <span v-for="i in 5" :key="i" class="text-yellow-400 text-xl">⭐</span>
            </div>
            <p class="text-gray-700 mb-6 italic">
              "Troisième commande et toujours satisfait. La livraison est gratuite et rapide. Les produits correspondent parfaitement aux descriptions."
            </p>
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center text-2xl">
                👨‍🔧
              </div>
              <div>
                <div class="font-bold text-gray-800">Patrick L.</div>
                <div class="text-sm text-gray-600">Brazzaville, RDC</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Newsletter -->
    <section class="py-16 bg-gradient-to-r from-orange-500 to-orange-600 text-white">
      <div class="container mx-auto px-4">
        <div class="max-w-3xl mx-auto text-center space-y-6">
          <h2 class="text-4xl font-bold">
            Restez Informé
          </h2>
          <p class="text-xl text-white/90">
            Inscrivez-vous à notre newsletter pour recevoir nos offres exclusives et nouveautés
          </p>
          
          <form @submit.prevent="inscrireNewsletter" class="flex flex-col sm:flex-row gap-4 max-w-xl mx-auto">
            <input 
              v-model="newsletterEmail"
              type="email"
              required
              placeholder="votre@email.com"
              class="flex-1 px-6 py-4 rounded-full text-gray-800 focus:outline-none focus:ring-4 focus:ring-white/50"
            />
            <button 
              type="submit"
              class="bg-white text-orange-600 px-8 py-4 rounded-full font-bold hover:bg-yellow-50 transition transform hover:scale-105"
            >
              S'inscrire
            </button>
          </form>
          
          <p v-if="newsletterMessage" class="text-sm" :class="newsletterSucces ? 'text-green-200' : 'text-red-200'">
            {{ newsletterMessage }}
          </p>
        </div>
      </div>
    </section>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useHead } from '#app'

// Meta tags pour SEO
useHead({
  title: 'Ets La Lumière - Boutique en ligne d\'éclairage professionnel',
  meta: [
    { 
      name: 'description', 
      content: 'Découvrez +10 000 produits d\'éclairage professionnel. Livraison gratuite partout en RDC. Paiement à la livraison. Garantie 2 ans. Leader depuis 2010.' 
    },
    { property: 'og:title', content: 'Ets La Lumière - Éclairage Professionnel RDC' },
    { property: 'og:description', content: 'Boutique en ligne leader en RDC. +10 000 produits, livraison gratuite, paiement à la livraison.' },
    { property: 'og:type', content: 'website' }
  ]
})

// État
const heroImageLoaded = ref(true)
const newsletterEmail = ref('')
const newsletterMessage = ref('')
const newsletterSucces = ref(false)

// Catégories (à charger depuis Firestore)
const categories = ref([
  { nom: 'Ampoules LED', icone: '💡', nombre: 250 },
  { nom: 'Projecteurs', icone: '🔦', nombre: 180 },
  { nom: 'Luminaires', icone: '🪔', nombre: 320 },
  { nom: 'Câbles & Accessoires', icone: '🔌', nombre: 450 },
  { nom: 'Panneaux Solaires', icone: '☀️', nombre: 95 },
  { nom: 'Générateurs', icone: '⚡', nombre: 60 }
])

// Produits vedettes (à charger depuis Firestore)
const produitsVedettes = ref([])
const nouveautes = ref([])

// Charger les produits
onMounted(async () => {
  try {
    const { $firestore } = useNuxtApp()
    
    // Charger les vedettes (top 8 par nombre_ventes)
    const vedettesSnapshot = await $firestore.getCollection('articles_publics', {
      where: [['est_publie', '==', true]],
      orderBy: ['nombre_ventes', 'desc'],
      limit: 8
    })
    
    produitsVedettes.value = vedettesSnapshot.docs.map(doc => ({
      code: doc.id,
      ...doc.data()
    }))
    
    // Charger les nouveautés (8 derniers par date_mise_a_jour)
    const nouveautesSnapshot = await $firestore.getCollection('articles_publics', {
      where: [['est_publie', '==', true]],
      orderBy: ['date_mise_a_jour', 'desc'],
      limit: 8
    })
    
    nouveautes.value = nouveautesSnapshot.docs.map(doc => ({
      code: doc.id,
      ...doc.data()
    }))
    
  } catch (error) {
    console.error('Erreur chargement produits:', error)
  }
})

// Formatage prix
function formatPrix(prix: number) {
  return new Intl.NumberFormat('fr-FR').format(prix)
}

// Ajouter au panier
function ajouterAuPanier(produit: any) {
  const { $cart } = useNuxtApp()
  $cart.add(produit)
  
  // Feedback visuel (toast ou animation)
  // TODO: Ajouter notification
}

// Newsletter
async function inscrireNewsletter() {
  try {
    const { $firestore } = useNuxtApp()
    
    await $firestore.addDocument('newsletter_subscribers', {
      email: newsletterEmail.value,
      date_inscription: new Date().toISOString(),
      actif: true
    })
    
    newsletterSucces.value = true
    newsletterMessage.value = '✓ Merci ! Vous êtes maintenant inscrit à notre newsletter.'
    newsletterEmail.value = ''
    
    // Cacher le message après 5s
    setTimeout(() => {
      newsletterMessage.value = ''
    }, 5000)
    
  } catch (error) {
    newsletterSucces.value = false
    newsletterMessage.value = '✗ Erreur lors de l\'inscription. Veuillez réessayer.'
    console.error('Erreur newsletter:', error)
  }
}
</script>

<style scoped>
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>