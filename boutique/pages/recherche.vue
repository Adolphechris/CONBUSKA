<template>
  <div class="py-8 bg-gray-50">
    <div class="container mx-auto px-4">
      <h1 class="text-3xl font-bold text-gray-800 mb-8">
        Résultats pour: "{{ query }}"
      </h1>

      <div v-if="loading" class="text-center py-12">
        <p class="text-gray-600">Recherche en cours...</p>
      </div>

      <div v-else-if="error" class="text-center py-12">
        <p class="text-red-600">{{ error }}</p>
      </div>

      <div v-else-if="articles.length === 0" class="text-center py-12">
        <p class="text-gray-600">Aucun résultat trouvé pour "{{ query }}"</p>
      </div>

      <template v-else>
        <p class="text-gray-600 mb-6">{{ articles.length }} résultat(s) trouvé(s)</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          <div
            v-for="article in articles"
            :key="article.id"
            class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow cursor-pointer"
            @click="goToArticle(article.code)"
          >
            <div class="h-48 bg-gray-200 flex items-center justify-center">
              <img
                v-if="article.image_url"
                :src="article.image_url"
                :alt="article.nom"
                class="w-full h-full object-cover"
                @error="handleImageError"
              />
              <svg v-else class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
            </div>
            <div class="p-4">
              <h3 class="font-semibold text-gray-800 mb-2 line-clamp-2">{{ article.nom }}</h3>
              <p class="text-orange-600 font-bold text-lg mb-2">{{ formatPrice(article.prix_vente) }}</p>
              <span class="text-sm text-gray-500">{{ article.categorie_nom }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { rechercherArticles } from '@/services/api'

const route = useRoute()
const router = useRouter()

const query = computed(() => route.params.query as string)
const articles = ref<any[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    loading.value = true
    error.value = null
    const data = await rechercherArticles(query.value)
    articles.value = data
  } catch (e) {
    console.error('Error searching articles:', e)
    error.value = 'Erreur lors de la recherche'
    articles.value = []
  } finally {
    loading.value = false
  }
})

const goToArticle = (code: string) => {
  router.push(`/produit/${code}`)
}

const formatPrice = (price: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(price)
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

// SEO
useHead({
  title: `Recherche: ${query.value} - Ets La Lumière`,
  meta: [
    { name: 'description', content: `Résultats de recherche pour "${query.value}" sur Ets La Lumière.` }
  ]
})
</script>