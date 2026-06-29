<template>
  <div class="py-8 bg-gray-50">
    <div class="container mx-auto px-4">
      <h1 class="text-3xl font-bold text-gray-800 mb-8">
        Mon Panier
      </h1>

      <div v-if="cartStore.isEmpty" class="text-center py-12 bg-white rounded-lg shadow-md">
        <p class="text-gray-600 mb-4">Votre panier est vide</p>
        <NuxtLink
          to="/"
          class="inline-block bg-orange-500 hover:bg-orange-600 text-white font-medium py-2 px-6 rounded-lg transition-colors"
        >
          Continuer vos achats
        </NuxtLink>
      </div>

      <div v-else>
        <div class="bg-white rounded-lg shadow-md overflow-hidden">
          <table class="w-full">
            <thead class="bg-gray-100">
              <tr>
                <th class="px-6 py-3 text-left text-gray-700 font-semibold">Produit</th>
                <th class="px-6 py-3 text-left text-gray-700 font-semibold">Prix</th>
                <th class="px-6 py-3 text-left text-gray-700 font-semibold">Quantité</th>
                <th class="px-6 py-3 text-left text-gray-700 font-semibold">Total</th>
                <th class="px-6 py-3 text-left text-gray-700 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in cartStore.items" :key="item.code_article" class="border-t">
                <td class="px-6 py-4">
                  <div class="flex items-center space-x-4">
                    <img
                      :src="item.image_url"
                      :alt="item.nom"
                      class="w-16 h-16 object-cover rounded"
                    />
                    <span class="font-medium text-gray-800">{{ item.nom }}</span>
                  </div>
                </td>
                <td class="px-6 py-4 text-gray-700">
                  {{ formatPrice(item.prix_unitaire) }}
                </td>
                <td class="px-6 py-4">
                  <div class="flex items-center space-x-2">
                    <button
                      @click="updateQuantity(item.code_article, item.quantite - 1)"
                      :disabled="item.quantite <= 1"
                      class="w-8 h-8 rounded-full bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      -
                    </button>
                    <span class="w-12 text-center">{{ item.quantite }}</span>
                    <button
                      @click="updateQuantity(item.code_article, item.quantite + 1)"
                      class="w-8 h-8 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center"
                    >
                      +
                    </button>
                  </div>
                </td>
                <td class="px-6 py-4 font-semibold text-gray-800">
                  {{ formatPrice(item.prix_unitaire * item.quantite) }}
                </td>
                <td class="px-6 py-4">
                  <button
                    @click="removeItem(item.code_article)"
                    class="text-red-600 hover:text-red-800"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Cart Summary -->
        <div class="mt-8 bg-white rounded-lg shadow-md p-6">
          <div class="flex justify-between items-center mb-4">
            <span class="text-xl font-semibold text-gray-800">Total:</span>
            <span class="text-3xl font-bold text-orange-600">
              {{ formatPrice(cartStore.totalPrice) }}
            </span>
          </div>
          
          <div class="flex justify-between items-center">
            <NuxtLink
              to="/"
              class="text-orange-600 hover:text-orange-800 font-medium"
            >
              ← Continuer vos achats
            </NuxtLink>
            
            <NuxtLink
              to="/checkout"
              class="bg-orange-500 hover:bg-orange-600 text-white font-medium py-3 px-8 rounded-lg transition-colors"
            >
              Passer la commande
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const cartStore = useCartStore()

const formatPrice = (price: number) => {
  const config = useRuntimeConfig()
  const currency = config.public.currency || 'CDF'
  return `${price.toLocaleString('fr-FR')} ${currency}`
}

const updateQuantity = (code_article: string, quantite: number) => {
  if (quantite >= 1) {
    cartStore.updateQuantity(code_article, quantite)
  }
}

const removeItem = (code_article: string) => {
  if (confirm('Êtes-vous sûr de vouloir supprimer cet article ?')) {
    cartStore.removeItem(code_article)
  }
}

// SEO
useHead({
  title: 'Mon Panier - Ets La Lumière',
  meta: [
    { name: 'description', content: 'Consultez votre panier et finalisez votre commande.' }
  ]
})
</script>