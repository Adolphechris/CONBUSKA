<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    
    <main class="py-12">
      <div class="container mx-auto px-4">
        <!-- Hero Section -->
        <div class="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 md:p-12 mb-12 text-white">
          <h1 class="text-4xl md:text-5xl font-bold mb-4">
            Livraison & Retours
          </h1>
          <p class="text-xl md:text-2xl opacity-90">
            Nous nous engageons à vous livrer rapidement et en toute sécurité
          </p>
        </div>

        <div class="max-w-4xl mx-auto">
          <!-- Zones de livraison -->
          <section class="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              📦 Zones de Livraison
            </h2>
            <div class="space-y-4">
              <div class="border-l-4 border-orange-500 pl-4">
                <h3 class="font-bold text-gray-800 mb-2">Kinshasa</h3>
                <p class="text-gray-600">
                  Livraison en 24-48h sur tout le territoire de Kinshasa.
                  <span class="text-green-600 font-semibold">Frais de livraison : GRATUITS</span>
                </p>
              </div>
              
              <div class="border-l-4 border-orange-500 pl-4">
                <h3 class="font-bold text-gray-800 mb-2">Provinces (Brazzaville, Matadi, Lubumbashi...)</h3>
                <p class="text-gray-600">
                  Livraison en 3-5 jours ouvrables via nos partenaires de transport.
                  <span class="text-green-600 font-semibold">Frais de livraison : GRATUITS</span>
                </p>
              </div>

              <div class="border-l-4 border-orange-500 pl-4">
                <h3 class="font-bold text-gray-800 mb-2">Autres villes du Congo</h3>
                <p class="text-gray-600">
                  Livraison en 5-7 jours ouvrables.
                  <span class="text-green-600 font-semibold">Frais de livraison : GRATUITS</span>
                </p>
              </div>
            </div>
          </section>

          <!-- Délais de livraison -->
          <section class="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              ⏱️ Délais de Livraison
            </h2>
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="bg-orange-50">
                    <th class="px-4 py-3 text-left text-gray-800 font-semibold">Zone</th>
                    <th class="px-4 py-3 text-left text-gray-800 font-semibold">Délai</th>
                    <th class="px-4 py-3 text-left text-gray-800 font-semibold">Frais</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                  <tr>
                    <td class="px-4 py-3 text-gray-700">Kinshasa</td>
                    <td class="px-4 py-3 text-gray-700">24-48h</td>
                    <td class="px-4 py-3 text-green-600 font-semibold">Gratuit</td>
                  </tr>
                  <tr class="bg-gray-50">
                    <td class="px-4 py-3 text-gray-700">Grandes villes</td>
                    <td class="px-4 py-3 text-gray-700">3-5 jours</td>
                    <td class="px-4 py-3 text-green-600 font-semibold">Gratuit</td>
                  </tr>
                  <tr>
                    <td class="px-4 py-3 text-gray-700">Autres villes</td>
                    <td class="px-4 py-3 text-gray-700">5-7 jours</td>
                    <td class="px-4 py-3 text-green-600 font-semibold">Gratuit</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p class="text-sm text-gray-500 mt-4">
              * Les délais sont donnés à titre indicatif et peuvent varier selon les conditions logistiques.
            </p>
          </section>

          <!-- Suivi de commande -->
          <section class="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              🔍 Suivi de Commande
            </h2>
            <p class="text-gray-600 mb-4">
              Une fois votre commande expédiée, vous recevrez un numéro de suivi par email. 
              Vous pourrez suivre votre colis en temps réel sur le site de notre partenaire de livraison.
            </p>
            <div class="bg-orange-50 border-l-4 border-orange-500 p-4 rounded">
              <p class="text-gray-700">
                <strong>Besoin d'aide ?</strong> Contactez notre service client au 
                <a href="tel:+243812345678" class="text-orange-500 hover:underline">+243 81 234 56 78</a> 
                ou par email à 
                <a href="mailto:livraison@etslumiere.cd" class="text-orange-500 hover:underline">livraison@etslumiere.cd</a>
              </p>
            </div>
          </section>

          <!-- Politique de retour -->
          <section class="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              ↩️ Politique de Retour
            </h2>
            
            <div class="space-y-6">
              <div>
                <h3 class="text-xl font-bold text-gray-800 mb-3">
                  Conditions de retour
                </h3>
                <ul class="list-disc list-inside space-y-2 text-gray-600">
                  <li>Le produit doit être dans son emballage d'origine</li>
                  <li>Le produit ne doit pas avoir été utilisé ou endommagé</li>
                  <li>Le retour doit être effectué dans un délai de <strong>7 jours</strong> après réception</li>
                  <li>Le produit doit être accompagné de la facture</li>
                </ul>
              </div>

              <div>
                <h3 class="text-xl font-bold text-gray-800 mb-3">
                  Procédure de retour
                </h3>
                <ol class="list-decimal list-inside space-y-2 text-gray-600">
                  <li>Contactez notre service client pour initier le retour</li>
                  <li>Emballez soigneusement le produit dans son emballage d'origine</li>
                  <li>Joignez la facture et un mot expliquant le motif du retour</li>
                  <li>Envoyez le colis à notre adresse :</li>
                </ol>
                <div class="bg-gray-50 p-4 rounded mt-3 ml-8">
                  <p class="text-gray-700">
                    <strong>Ets La Lumière</strong><br />
                    123 Avenue de l'Indépendance<br />
                    Kinshasa, RDC
                  </p>
                </div>
              </div>

              <div>
                <h3 class="text-xl font-bold text-gray-800 mb-3">
                  Remboursement
                </h3>
                <p class="text-gray-600">
                  Une fois le produit reçu et vérifié, nous procéderons au remboursement 
                  dans un délai de 7-10 jours ouvrables. Le remboursement sera effectué 
                  sur le même mode de paiement que celui utilisé lors de l'achat.
                </p>
              </div>

              <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
                <h3 class="text-lg font-bold text-gray-800 mb-2">
                  ⚠️ Cas non remboursables
                </h3>
                <ul class="list-disc list-inside space-y-1 text-gray-600">
                  <li>Produits endommagés ou utilisés</li>
                  <li>Retour effectué après le délai de 7 jours</li>
                  <li>Produits personnalisés ou sur mesure</li>
                </ul>
              </div>
            </div>
          </section>

          <!-- FAQ Livraison -->
          <section class="bg-white rounded-lg shadow-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              ❓ Questions Fréquentes
            </h2>
            <div class="space-y-4">
              <div class="border-b border-gray-200 pb-4">
                <h3 class="font-bold text-gray-800 mb-2">
                  Comment suivre ma commande ?
                </h3>
                <p class="text-gray-600">
                  Vous recevrez un email avec un numéro de suivi dès que votre commande sera expédiée.
                </p>
              </div>
              
              <div class="border-b border-gray-200 pb-4">
                <h3 class="font-bold text-gray-800 mb-2">
                  Que faire si je ne suis pas là lors de la livraison ?
                </h3>
                <p class="text-gray-600">
                  Le livreur tentera de vous contacter. Vous pourrez convenir d'un nouveau créneau 
                  ou retirer votre colis au point de livraison le plus proche.
                </p>
              </div>

              <div class="border-b border-gray-200 pb-4">
                <h3 class="font-bold text-gray-800 mb-2">
                  Les frais de livraison sont-ils vraiment gratuits ?
                </h3>
                <p class="text-gray-600">
                  Oui, tous nos produits bénéficient de la livraison gratuite sur tout le territoire 
                  de la RDC, sans minimum d'achat.
                </p>
              </div>

              <div>
                <h3 class="font-bold text-gray-800 mb-2">
                  Puis-je modifier mon adresse de livraison après commande ?
                </h3>
                <p class="text-gray-600">
                  Oui, contactez-nous immédiatement au +243 81 234 56 78. Si la commande n'a pas 
                  encore été expédiée, nous pourrons modifier l'adresse sans frais supplémentaires.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
// Meta tags pour SEO
useHead({
  title: 'Livraison & Retours - Ets La Lumière',
  meta: [
    { name: 'description', content: 'Informations sur la livraison et les retours chez Ets La Lumière. Livraison gratuite partout en RDC, délais 24-48h à Kinshasa, retour sous 7 jours.' }
  ]
})
</script>