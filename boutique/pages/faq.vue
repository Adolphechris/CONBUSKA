<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    
    <main class="py-12">
      <div class="container mx-auto px-4">
        <!-- Hero Section -->
        <div class="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 md:p-12 mb-12 text-white">
          <h1 class="text-4xl md:text-5xl font-bold mb-4">
            Questions Fréquentes
          </h1>
          <p class="text-xl md:text-2xl opacity-90">
            Trouvez rapidement les réponses à vos questions
          </p>
        </div>

        <div class="max-w-4xl mx-auto">
          <!-- Barre de recherche FAQ -->
          <div class="mb-8">
            <div class="relative">
              <input 
                v-model="recherche"
                type="text"
                placeholder="Rechercher une question..."
                class="w-full px-6 py-4 pl-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent text-lg"
              />
              <span class="absolute left-4 top-1/2 transform -translate-y-1/2 text-2xl">🔍</span>
            </div>
          </div>

          <!-- Catégories de FAQ -->
          <div class="space-y-8">
            <!-- Commandes -->
            <section class="bg-white rounded-lg shadow-lg p-8">
              <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                <span class="text-3xl mr-3">🛒</span>
                Commandes
              </h2>
              <div class="space-y-4">
                <div v-for="(item, index) in faqCommandesFiltree" :key="'cmd-'+index" class="border-b border-gray-200 pb-4 last:border-0">
                  <h3 
                    class="font-bold text-gray-800 mb-2 cursor-pointer flex items-center justify-between"
                    @click="toggleFaq('cmd-'+index)"
                  >
                    <span>{{ item.q }}</span>
                    <span class="text-orange-500 text-xl">{{ item.open ? '−' : '+' }}</span>
                  </h3>
                  <div v-show="item.open" class="text-gray-600 mt-2 pl-4">
                    {{ item.r }}
                  </div>
                </div>
              </div>
            </section>

            <!-- Paiement -->
            <section class="bg-white rounded-lg shadow-lg p-8">
              <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                <span class="text-3xl mr-3">💳</span>
                Paiement
              </h2>
              <div class="space-y-4">
                <div v-for="(item, index) in faqPaiementFiltree" :key="'pay-'+index" class="border-b border-gray-200 pb-4 last:border-0">
                  <h3 
                    class="font-bold text-gray-800 mb-2 cursor-pointer flex items-center justify-between"
                    @click="toggleFaq('pay-'+index)"
                  >
                    <span>{{ item.q }}</span>
                    <span class="text-orange-500 text-xl">{{ item.open ? '−' : '+' }}</span>
                  </h3>
                  <div v-show="item.open" class="text-gray-600 mt-2 pl-4">
                    {{ item.r }}
                  </div>
                </div>
              </div>
            </section>

            <!-- Livraison -->
            <section class="bg-white rounded-lg shadow-lg p-8">
              <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                <span class="text-3xl mr-3">🚚</span>
                Livraison
              </h2>
              <div class="space-y-4">
                <div v-for="(item, index) in faqLivraisonFiltree" :key="'liv-'+index" class="border-b border-gray-200 pb-4 last:border-0">
                  <h3 
                    class="font-bold text-gray-800 mb-2 cursor-pointer flex items-center justify-between"
                    @click="toggleFaq('liv-'+index)"
                  >
                    <span>{{ item.q }}</span>
                    <span class="text-orange-500 text-xl">{{ item.open ? '−' : '+' }}</span>
                  </h3>
                  <div v-show="item.open" class="text-gray-600 mt-2 pl-4">
                    {{ item.r }}
                  </div>
                </div>
              </div>
            </section>

            <!-- Produits -->
            <section class="bg-white rounded-lg shadow-lg p-8">
              <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                <span class="text-3xl mr-3">💡</span>
                Produits
              </h2>
              <div class="space-y-4">
                <div v-for="(item, index) in faqProduitsFiltree" :key="'prod-'+index" class="border-b border-gray-200 pb-4 last:border-0">
                  <h3 
                    class="font-bold text-gray-800 mb-2 cursor-pointer flex items-center justify-between"
                    @click="toggleFaq('prod-'+index)"
                  >
                    <span>{{ item.q }}</span>
                    <span class="text-orange-500 text-xl">{{ item.open ? '−' : '+' }}</span>
                  </h3>
                  <div v-show="item.open" class="text-gray-600 mt-2 pl-4">
                    {{ item.r }}
                  </div>
                </div>
              </div>
            </section>

            <!-- Retours -->
            <section class="bg-white rounded-lg shadow-lg p-8">
              <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                <span class="text-3xl mr-3">↩️</span>
                Retours & SAV
              </h2>
              <div class="space-y-4">
                <div v-for="(item, index) in faqRetoursFiltree" :key="'ret-'+index" class="border-b border-gray-200 pb-4 last:border-0">
                  <h3 
                    class="font-bold text-gray-800 mb-2 cursor-pointer flex items-center justify-between"
                    @click="toggleFaq('ret-'+index)"
                  >
                    <span>{{ item.q }}</span>
                    <span class="text-orange-500 text-xl">{{ item.open ? '−' : '+' }}</span>
                  </h3>
                  <div v-show="item.open" class="text-gray-600 mt-2 pl-4">
                    {{ item.r }}
                  </div>
                </div>
              </div>
            </section>
          </div>

          <!-- Contact CTA -->
          <div class="mt-12 bg-orange-50 rounded-lg p-8 text-center">
            <h3 class="text-2xl font-bold text-gray-800 mb-4">
              Vous n'avez pas trouvé la réponse ?
            </h3>
            <p class="text-gray-600 mb-6">
              Notre équipe est disponible 24/7 pour répondre à toutes vos questions
            </p>
            <a 
              href="/contact" 
              class="inline-block bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 px-8 rounded-lg transition duration-200"
            >
              Contactez-nous
            </a>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useHead } from '#app'

// Meta tags pour SEO
useHead({
  title: 'FAQ - Ets La Lumière',
  meta: [
    { name: 'description', content: 'Questions fréquentes sur les commandes, paiements, livraisons et retours chez Ets La Lumière. Trouvez rapidement des réponses.' }
  ]
})

// Recherche
const recherche = ref('')

// FAQ Data
const faqCommandes = ref([
  { 
    q: 'Comment passer une commande ?', 
    r: 'C\'est simple ! Parcourez notre catalogue, ajoutez les produits à votre panier, puis cliquez sur "Commander". Remplissez le formulaire avec vos coordonnées et validez. Vous recevrez une confirmation par email.',
    open: false 
  },
  { 
    q: 'Puis-je modifier ma commande après validation ?', 
    r: 'Une fois la commande validée, vous ne pouvez plus la modifier directement. Contactez immédiatement notre service client au +243 81 234 56 78. Si la commande n\'a pas encore été expédiée, nous pourrons l\'annuler et vous devrez passer une nouvelle commande.',
    open: false 
  },
  { 
    q: 'Comment annuler ma commande ?', 
    r: 'Vous pouvez annuler votre commande dans un délai de 2h après validation, tant qu\'elle n\'a pas été expédiée. Contactez notre service client par téléphone ou email. Passé ce délai, la commande ne pourra plus être annulée mais pourra être retournée selon notre politique de retour.',
    open: false 
  },
  { 
    q: 'Comment obtenir une facture ?', 
    r: 'La facture est automatiquement générée et envoyée par email après validation de votre commande. Vous pouvez également la télécharger depuis votre espace client ou la demander à nouveau à notre service client.',
    open: false 
  }
])

const faqPaiement = ref([
  { 
    q: 'Quels modes de paiement acceptez-vous ?', 
    r: 'Actuellement, nous acceptons uniquement le paiement à la livraison ou en magasin. Le paiement en ligne (carte bancaire, mobile money) sera disponible prochainement.',
    open: false 
  },
  { 
    q: 'Le paiement est-il sécurisé ?', 
    r: 'Oui, lorsque le paiement en ligne sera disponible, il sera sécurisé par nos partenaires de paiement certifiés (Stripe, PayPal, etc.). Aucune donnée bancaire ne transite par nos serveurs.',
    open: false 
  },
  { 
    q: 'Puis-je payer en plusieurs fois ?', 
    r: 'Non, pour l\'instant nous n\'offrons pas de paiement échelonné. Le paiement s\'effectue en une seule fois à la livraison ou en magasin.',
    open: false 
  }
])

const faqLivraison = ref([
  { 
    q: 'Quels sont les délais de livraison ?', 
    r: 'À Kinshasa : 24-48h. Dans les grandes villes : 3-5 jours ouvrables. Dans les autres villes : 5-7 jours ouvrables. Ces délais sont donnés à titre indicatif et peuvent varier selon les conditions logistiques.',
    open: false 
  },
  { 
    q: 'La livraison est-elle vraiment gratuite ?', 
    r: 'Oui, la livraison est gratuite sur tout le territoire de la RDC, sans minimum d\'achat. Nous prenons en charge tous les frais de livraison.',
    open: false 
  },
  { 
    q: 'Comment suivre ma commande ?', 
    r: 'Dès que votre commande est expédiée, vous recevez un email avec un numéro de suivi. Vous pouvez suivre votre colis en temps réel sur le site de notre partenaire de livraison.',
    open: false 
  },
  { 
    q: 'Puis-je choisir mon créneau de livraison ?', 
    r: 'Oui, lors de la validation de votre commande, vous pouvez indiquer vos préférences de créneau. Le livreur vous contactera pour confirmer l\'heure de passage.',
    open: false 
  }
])

const faqProduits = ref([
  { 
    q: 'Les produits sont-ils garantis ?', 
    r: 'Oui, tous nos produits bénéficient de la garantie constructeur. La durée de garantie varie selon les produits (généralement 1 à 2 ans). Consultez la fiche produit pour plus de détails.',
    open: false 
  },
  { 
    q: 'Comment choisir le bon produit ?', 
    r: 'Notre équipe d\'experts est disponible pour vous conseiller. Vous pouvez nous contacter par téléphone, email ou via le formulaire de contact. Nous vous aiderons à choisir le produit le plus adapté à vos besoins.',
    open: false 
  },
  { 
    q: 'Proposez-vous des produits sur mesure ?', 
    r: 'Pour certains produits, nous proposons des solutions personnalisées. Contactez-nous avec votre projet et nous vous proposerons une solution adaptée.',
    open: false 
  },
  { 
    q: 'Les photos des produits sont-elles conformes ?', 
    r: 'Nous nous efforçons de présenter des photos les plus fidèles possible. Cependant, des différences de couleur peuvent apparaître selon votre écran. N\'hésitez pas à nous contacter pour plus de détails sur un produit.',
    open: false 
  }
])

const faqRetours = ref([
  { 
    q: 'Quelle est la politique de retour ?', 
    r: 'Vous disposez de 7 jours après réception pour retourner un produit. Le produit doit être dans son emballage d\'origine, non utilisé et non endommagé. Consultez notre page Livraison & Retours pour plus de détails.',
    open: false 
  },
  { 
    q: 'Comment effectuer un retour ?', 
    r: 'Contactez notre service client pour initier le retour. Emballez le produit dans son emballage d\'origine avec la facture, puis envoyez-le à notre adresse. Nous vous rembourserons dans un délai de 7-10 jours ouvrables après réception et vérification.',
    open: false 
  },
  { 
    q: 'Les frais de retour sont-ils à ma charge ?', 
    r: 'Oui, les frais de retour sont à la charge du client, sauf en cas de produit défectueux ou d\'erreur de notre part. Dans ce cas, nous prenons en charge les frais de retour et de réexpédition.',
    open: false 
  },
  { 
    q: 'Que faire si je reçois un produit défectueux ?', 
    r: 'Contactez immédiatement notre service client avec des photos du défaut. Nous vous proposerons soit un échange, soit un remboursement intégral, frais de retour inclus.',
    open: false 
  }
])

// Toggle FAQ
function toggleFaq(id: string) {
  const allFaqs = [
    ...faqCommandes.value,
    ...faqPaiement.value,
    ...faqLivraison.value,
    ...faqProduits.value,
    ...faqRetours.value
  ]
  
  const item = allFaqs.find((_, index) => {
    const keys = [
      ...faqCommandes.value.map((_, i) => 'cmd-' + i),
      ...faqPaiement.value.map((_, i) => 'pay-' + i),
      ...faqLivraison.value.map((_, i) => 'liv-' + i),
      ...faqProduits.value.map((_, i) => 'prod-' + i),
      ...faqRetours.value.map((_, i) => 'ret-' + i)
    ]
    return keys[index] === id
  })
  
  if (item) {
    item.open = !item.open
  }
}

// FAQ filtrées par recherche
const faqCommandesFiltree = computed(() => filterFaq(faqCommandes.value))
const faqPaiementFiltree = computed(() => filterFaq(faqPaiement.value))
const faqLivraisonFiltree = computed(() => filterFaq(faqLivraison.value))
const faqProduitsFiltree = computed(() => filterFaq(faqProduits.value))
const faqRetoursFiltree = computed(() => filterFaq(faqRetours.value))

function filterFaq(items: any[]) {
  if (!recherche.value) return items
  
  const search = recherche.value.toLowerCase()
  return items.map(item => ({
    ...item,
    open: item.q.toLowerCase().includes(search) || item.r.toLowerCase().includes(search)
  })).filter(item => 
    item.q.toLowerCase().includes(search) || item.r.toLowerCase().includes(search)
  )
}
</script>