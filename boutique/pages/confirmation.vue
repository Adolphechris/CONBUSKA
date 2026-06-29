<template>
  <div class="py-8 bg-gray-50">
    <div class="container mx-auto px-4">
      <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-8">
        <div class="text-center mb-6">
          <svg class="w-20 h-20 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <h1 class="text-3xl font-bold text-gray-800 mb-2">Commande confirmée !</h1>
          <p class="text-gray-600">Merci pour votre achat</p>
        </div>

        <div class="bg-gray-50 rounded-lg p-6 mb-6">
          <h2 class="text-xl font-semibold mb-4">Récapitulatif de la commande</h2>
          
          <div class="space-y-2 mb-4">
            <div class="flex justify-between">
              <span class="text-gray-600">Numéro de facture:</span>
              <span class="font-semibold">{{ orderData?.facture_code || 'N/A' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Total USD:</span>
              <span class="font-semibold">{{ formatPrice(orderData?.total_usd || 0) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Total FC:</span>
              <span class="font-semibold">{{ formatFC(orderData?.total_fc || 0) }}</span>
            </div>
          </div>
        </div>

        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p class="text-sm text-blue-800">
            <strong>Note:</strong> Votre commande a été enregistrée dans notre système. 
            Vous serez contacté par téléphone pour confirmer la livraison.
          </p>
        </div>

        <div class="flex flex-col sm:flex-row gap-4">
          <NuxtLink to="/" class="flex-1 bg-orange-500 text-white text-center px-6 py-3 rounded-lg font-semibold hover:bg-orange-600 transition-colors">
            Continuer mes achats
          </NuxtLink>
          <button @click="printReceipt" class="flex-1 bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-600 transition-colors">
            Imprimer le reçu
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const orderData = ref<any>(null)

onMounted(() => {
  // Récupérer les données de la commande depuis le state ou localStorage
  const stored = localStorage.getItem('lastOrder')
  if (stored) {
    orderData.value = JSON.parse(stored)
    localStorage.removeItem('lastOrder')
  }
})

const formatPrice = (price: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(price)
}

const formatFC = (price: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'CDF',
    minimumFractionDigits: 2
  }).format(price)
}

const printReceipt = () => {
  window.print()
}

// SEO
useHead({
  title: 'Commande confirmée - Ets La Lumière',
  meta: [
    { name: 'description', content: 'Votre commande a été confirmée avec succès. Merci pour votre achat chez Ets La Lumière.' }
  ]
})
</script>