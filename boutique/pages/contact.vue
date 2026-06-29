<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    
    <main class="py-12">
      <div class="container mx-auto px-4">
        <!-- Hero Section -->
        <div class="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 md:p-12 mb-12 text-white">
          <h1 class="text-4xl md:text-5xl font-bold mb-4">
            Contactez-nous
          </h1>
          <p class="text-xl md:text-2xl opacity-90">
            Notre équipe est à votre écoute 24/7
          </p>
        </div>

        <div class="grid md:grid-cols-2 gap-8">
          <!-- Formulaire de contact -->
          <div class="bg-white rounded-lg shadow-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              Envoyez-nous un message
            </h2>
            
            <form @submit.prevent="envoyerMessage" class="space-y-4">
              <div>
                <label class="block text-gray-700 font-medium mb-2">
                  Nom complet *
                </label>
                <input 
                  v-model="form.nom"
                  type="text" 
                  required
                  class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Votre nom"
                />
              </div>

              <div>
                <label class="block text-gray-700 font-medium mb-2">
                  Email *
                </label>
                <input 
                  v-model="form.email"
                  type="email" 
                  required
                  class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="votre@email.com"
                />
              </div>

              <div>
                <label class="block text-gray-700 font-medium mb-2">
                  Sujet
                </label>
                <input 
                  v-model="form.sujet"
                  type="text"
                  class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Sujet de votre message"
                />
              </div>

              <div>
                <label class="block text-gray-700 font-medium mb-2">
                  Message *
                </label>
                <textarea 
                  v-model="form.message"
                  required
                  rows="6"
                  class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
                  placeholder="Votre message..."
                ></textarea>
              </div>

              <button 
                type="submit"
                :disabled="envoiEnCours"
                class="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition duration-200"
              >
                {{ envoiEnCours ? 'Envoi en cours...' : 'Envoyer le message' }}
              </button>

              <div v-if="messageSucces" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
                ✓ {{ messageSucces }}
              </div>

              <div v-if="messageErreur" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                ✗ {{ messageErreur }}
              </div>
            </form>
          </div>

          <!-- Informations de contact -->
          <div class="space-y-6">
            <div class="bg-white rounded-lg shadow-lg p-8">
              <h2 class="text-2xl font-bold text-gray-800 mb-6">
                Nos Coordonnées
              </h2>
              
              <div class="space-y-4">
                <div class="flex items-start">
                  <span class="text-2xl mr-4">📍</span>
                  <div>
                    <h3 class="font-bold text-gray-800 mb-1">Adresse</h3>
                    <p class="text-gray-600">
                      123 Avenue de l'Indépendance<br />
                      Kinshasa, République Démocratique du Congo
                    </p>
                  </div>
                </div>

                <div class="flex items-start">
                  <span class="text-2xl mr-4">📞</span>
                  <div>
                    <h3 class="font-bold text-gray-800 mb-1">Téléphone</h3>
                    <p class="text-gray-600">
                      <a href="tel:+243123456789" class="hover:text-orange-500">
                        +243 81 234 56 78
                      </a>
                    </p>
                  </div>
                </div>

                <div class="flex items-start">
                  <span class="text-2xl mr-4">✉️</span>
                  <div>
                    <h3 class="font-bold text-gray-800 mb-1">Email</h3>
                    <p class="text-gray-600">
                      <a href="mailto:contact@etslumiere.cd" class="hover:text-orange-500">
                        contact@etslumiere.cd
                      </a>
                    </p>
                  </div>
                </div>

                <div class="flex items-start">
                  <span class="text-2xl mr-4">🕐</span>
                  <div>
                    <h3 class="font-bold text-gray-800 mb-1">Heures d'ouverture</h3>
                    <p class="text-gray-600">
                      Lundi - Vendredi : 8h00 - 18h00<br />
                      Samedi : 9h00 - 15h00<br />
                      Dimanche : Fermé
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Carte Google Maps -->
            <div class="bg-white rounded-lg shadow-lg p-4">
              <h3 class="text-xl font-bold text-gray-800 mb-4 px-2">
                Notre Localisation
              </h3>
              <div class="rounded-lg overflow-hidden">
                <iframe
                  src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3978.123456789!2d15.2667!3d-4.4417!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zNMKwMjcnMjguNCJOIDc1wrAyNSczMS4wIlc!5e0!3m2!1sfr!2scd!4v1234567890"
                  width="100%"
                  height="300"
                  style="border:0;"
                  allowfullscreen=""
                  loading="lazy"
                ></iframe>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useHead } from '#app'

// Meta tags pour SEO
useHead({
  title: 'Contact - Ets La Lumière',
  meta: [
    { name: 'description', content: 'Contactez Ets La Lumière à Kinshasa. Téléphone, email, adresse. Notre équipe est à votre écoute 24/7 pour tous vos besoins en éclairage.' }
  ]
})

// Form data
const form = ref({
  nom: '',
  email: '',
  sujet: '',
  message: ''
})

const envoiEnCours = ref(false)
const messageSucces = ref('')
const messageErreur = ref('')

// Envoyer le message
async function envoyerMessage() {
  envoiEnCours.value = true
  messageSucces.value = ''
  messageErreur.value = ''

  try {
    // Sauvegarder dans Firestore
    const { $firestore } = useNuxtApp()
    
    await $firestore.addDocument('contact_messages', {
      nom: form.value.nom,
      email: form.value.email,
      sujet: form.value.sujet,
      message: form.value.message,
      date: new Date().toISOString(),
      lu: false
    })

    messageSucces.value = 'Votre message a été envoyé avec succès ! Nous vous répondrons dans les plus brefs délais.'
    
    // Réinitialiser le formulaire
    form.value = {
      nom: '',
      email: '',
      sujet: '',
      message: ''
    }
  } catch (error) {
    console.error('Erreur envoi message:', error)
    messageErreur.value = 'Une erreur est survenue. Veuillez réessayer ou nous contacter directement par téléphone.'
  } finally {
    envoiEnCours.value = false
  }
}
</script>