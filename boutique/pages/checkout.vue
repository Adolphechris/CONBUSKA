<template>
  <div class="py-8 bg-gray-50">
    <div class="container mx-auto px-4">
      <h1 class="text-3xl font-bold text-gray-800 mb-8">Finaliser votre commande</h1>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Formulaire client -->
        <div class="lg:col-span-2">
          <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold mb-4">Informations de livraison</h2>
            
            <form @submit.prevent="submitOrder" class="space-y-4">
              <div>
                <label class="block text-gray-700 mb-2">Nom complet *</label>
                <input v-model="client.nom" type="text" required class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
              </div>

              <div>
                <label class="block text-gray-700 mb-2">Téléphone *</label>
                <input v-model="client.telephone" type="tel" required class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
              </div>

              <div>
                <label class="block text-gray-700 mb-2">Email</label>
                <input v-model="client.email" type="email" class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
              </div>

              <div>
                <label class="block text-gray-700 mb-2">Adresse *</label>
                <textarea v-model="client.adresse" required rows="3" class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"></textarea>
              </div>

              <div>
                <label class="block text-gray-700 mb-2">Ville</label>
                <input v-model="client.ville" type="text" class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500" />
              </div>

              <button type="submit" :disabled="submitting" class="w-full bg-orange-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors">
                {{ submitting ? 'Envoi en cours...' : 'Envoyer la commande par email' }}
              </button>
            </form>

            <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p class="text-sm text-blue-800">
                📧 Votre commande sera envoyée par email. Nous vous contacterons dans les plus brefs délais pour confirmer.
              </p>
            </div>
          </div>
        </div>

        <!-- Récapitulatif -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold mb-4">Récapitulatif</h2>
            
            <div class="space-y-3 mb-4">
              <div v-for="item in cart.items" :key="item.code_article" class="flex justify-between text-sm">
                <span>{{ item.nom }} x{{ item.quantite }}</span>
                <span>{{ formatPrice(item.prix_unitaire * item.quantite) }}</span>
              </div>
            </div>

            <div class="border-t pt-4">
              <div class="flex justify-between text-lg font-bold">
                <span>Total</span>
                <span class="text-orange-600">{{ formatPrice(cart.totalPrice) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Message de succès -->
      <div v-if="orderSuccess" class="mt-8 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
        <p class="font-semibold">✅ Commande envoyée avec succès !</p>
        <p class="mt-2">Nous avons bien reçu votre commande. Vous recevrez un email de confirmation sous peu.</p>
        <p class="mt-2 text-sm">Référence: {{ orderReference }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const cart = useCartStore()
const client = ref({
  nom: '',
  telephone: '',
  email: '',
  adresse: '',
  ville: 'Kinshasa'
})

const submitting = ref(false)
const orderSuccess = ref(false)
const orderReference = ref('')

const formatPrice = (price: number): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(price)
}

const submitOrder = async () => {
  if (cart.items.length === 0) {
    alert('Votre panier est vide')
    return
  }

  submitting.value = true

  try {
    // Générer une référence de commande
    const ref = 'CMD-' + Date.now().toString(36).toUpperCase()
    orderReference.value = ref

    // Préparer le message email
    const emailBody = `
Nouvelle commande depuis le site web

Référence: ${ref}

INFORMATIONS CLIENT:
- Nom: ${client.value.nom}
- Téléphone: ${client.value.telephone}
- Email: ${client.value.email}
- Adresse: ${client.value.adresse}
- Ville: ${client.value.ville}

ARTICLES COMMANDÉS:
${cart.items.map(item => `- ${item.nom} x${item.quantite} = ${formatPrice(item.prix_unitaire * item.quantite)}`).join('\n')}

TOTAL: ${formatPrice(cart.totalPrice)}

---
Commande passée le ${new Date().toLocaleString('fr-FR')}
    `.trim()

    // Ouvrir le client email par défaut
    const mailtoLink = `mailto:commande@etslumiere.cd?subject=Commande ${ref}&body=${encodeURIComponent(emailBody)}`
    window.open(mailtoLink, '_blank')

    orderSuccess.value = true
    
    // Sauvegarder la commande
    localStorage.setItem('lastOrder', JSON.stringify({
      reference: ref,
      client: client.value,
      items: cart.items,
      total: cart.totalPrice,
      date: new Date().toISOString()
    }))
    
    // Vider le panier
    cart.clear()
    
    // Réinitialiser le formulaire
    client.value = {
      nom: '',
      telephone: '',
      email: '',
      adresse: '',
      ville: 'Kinshasa'
    }

  } catch (error) {
    alert('Erreur: ' + (error as Error).message)
  } finally {
    submitting.value = false
  }
}

// SEO
useHead({
  title: 'Finaliser votre commande - Ets La Lumière',
  meta: [
    { name: 'description', content: 'Finalisez votre commande sur Ets La Lumière. Livraison partout au Congo.' }
  ]
})
</script>