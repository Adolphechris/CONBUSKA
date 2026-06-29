<template>
  <div class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
    <NuxtLink :to="`/produit/${article.code_article}`">
      <div class="relative aspect-square">
        <img
          :src="article.image_url || '/images/default-product.jpg'"
          :alt="article.nom"
          class="w-full h-full object-cover"
          loading="lazy"
        />
        <BadgeStock :stock="article.stock_disponible" :seuil="article.seuil_alerte" />
      </div>
      
      <div class="p-4">
        <h3 class="text-lg font-semibold text-gray-800 mb-2 line-clamp-2">
          {{ article.nom }}
        </h3>
        
        <p class="text-sm text-gray-600 mb-2">
          {{ article.categorie }}
        </p>
        
        <div class="flex items-center justify-between mb-3">
          <span class="text-xl font-bold text-orange-600">
            {{ formatPrice(article.prix) }}
          </span>
        </div>
        
        <button
          @click.prevent="addToCart"
          :disabled="article.stock_disponible === 0"
          class="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
        >
          {{ article.stock_disponible === 0 ? 'Rupture de stock' : 'Ajouter au panier' }}
        </button>
      </div>
    </NuxtLink>
  </div>
</template>

<script setup lang="ts">
import type { Article } from '~/types'
import BadgeStock from './BadgeStock.vue'

const props = defineProps<{
  article: Article
}>()

const cartStore = useCartStore()

const formatPrice = (price: number) => {
  const config = useRuntimeConfig()
  const currency = config.public.currency || 'CDF'
  return `${price.toLocaleString('fr-FR')} ${currency}`
}

const addToCart = () => {
  const config = useRuntimeConfig()
  const currency = config.public.currency || 'CDF'
  
  cartStore.addItem({
    code_article: props.article.code_article,
    nom: props.article.nom,
    prix_unitaire: props.article.prix,
    quantite: 1,
    image_url: props.article.image_url || '/images/default-product.jpg'
  })
  
  // Optionnel: afficher une notification
  alert('Produit ajouté au panier!')
}
</script>