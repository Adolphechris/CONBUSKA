<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    
    <main class="py-12">
      <div class="container mx-auto px-4">
        <!-- Hero Section -->
        <div class="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 md:p-12 mb-12 text-white">
          <h1 class="text-4xl md:text-5xl font-bold mb-4">
            Mentions Légales
          </h1>
          <p class="text-xl md:text-2xl opacity-90">
            Informations juridiques et réglementaires
          </p>
        </div>

        <div class="max-w-4xl mx-auto space-y-8">
          <!-- Identification -->
          <section class="bg-white rounded-lg shadow-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              1. Identification de l'entreprise
            </h2>
            <div class="space-y-3 text-gray-700">
              <p><strong>Raison sociale :</strong> Ets La Lumière</p>
              <p><strong>Forme juridique :</strong> Société à Responsabilité Limitée (SARL)</p>
              <p><strong>Capital social :</strong> 10.000.000 Francs Congolais (CDF)</p>
              <p><strong>RCCM :</strong> CD/KIN/RCCM/2020-A-1234</p>
              <p><strong>ID National :</strong> 123456789</p>
              <p><strong>Numéro d'impôt :</strong> 098765432</p>
              <p><strong>Adresse du siège social :</strong> 123 Avenue de l'Indépendance, Kinshasa, RDC</p>
              <p><strong>Téléphone :</strong> +243 81 234 56 78</p>
              <p><strong>Email :</strong> contact@etslumiere.cd</p>
              <p><strong>Directeur de publication :</strong> [Nom du gérant]</p>
            </div>
          </section>

          <!-- Hébergement -->
          <section class="bg-white rounded-lg shadow-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              2. Hébergement du site
            </h2>
            <div class="space-y-3 text-gray-700">
              <p><strong>Hébergeur :</strong> Firebase Hosting (Google LLC)</p>
              <p><strong>Adresse :</strong> 1600 Amphitheatre Parkway, Mountain View, CA 94043, USA</p>
              <p><strong>Site web :</strong> https://firebase.google.com</p>
            </div>
          </section>

          <!-- Propriété intellectuelle -->
          <section class="bg-white rounded-lg shadow-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              3. Propriété intellectuelle
            </h2>
            <div class="space-y-4 text-gray-700">
              <p>
                L'ensemble du contenu du site <strong>boutique.etslumiere.cd</strong> (textes, images, vidéos, logos, 
                icônes, sons, logiciels, etc.) est la propriété exclusive de <strong>Ets La Lumière</strong> ou de ses 
                partenaires, et est protégé par les lois relatives à la propriété intellectuelle.
              </p>
              <p>
                Toute reproduction, distribution, modification, adaptation, retransmission ou publication de ces 
                différents éléments est strictement interdite sans l'accord écrit préalable de Ets La Lumière.
              </p>
              <p>
                Les marques et logos figurant sur le site sont des marques déposées par Ets La Lumière ou ses 
                partenaires. Toute reproduction ou imitation de ces marques et logos est interdite.
              </p>
            </div>
          </section>

          <!-- Données personnelles -->
          <section class="bg-white rounded-lg shadow-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              4. Protection des données personnelles
            </h2>
            <div class="space-y-4 text-gray-700">
              <p>
                Conformément à la loi n° 23/020 du 13 mars 2023 relative à la protection des données personnelles 
                en République Démocratique du Congo, vous disposez d'un droit d'accès, de rectification, 
                d'effacement et d'opposition aux données vous concernant.
              </p>
              <p>
                Les données collectées sur ce site sont nécessaires au traitement de vos commandes et à 
                l'amélioration de nos services. Elles ne sont jamais transmises à des tiers sans votre consentement.
              </p>
              <p>
                Pour exercer vos droits ou pour toute question sur le traitement de vos données, contactez-nous 
                à l'adresse : <a href="mailto:privacy@etslumiere.cd" class="text-orange-500 hover:underline">privacy@etslumiere.cd</a>
              </p>
              <p>
                Pour plus d'informations, consultez notre 
                <NuxtLink to="/politique-confidentialite" class="text-orange-500 hover:underline">
                  Politique de Confidentialité
                </NuxtLink>.
              </p>
            </div>
          </section>

          <!-- Cookies -->
          <section class="bg-white rounded-lg shadow-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              5. Cookies
            </h2>
            <div class="space-y-4 text-gray-700">
              <p>
                Ce site utilise des cookies pour améliorer votre expérience de navigation. Les cookies sont 
                des petits fichiers textes stockés sur votre appareil.
              </p>
              <p>
                <strong>Types de cookies utilisés :</strong>
              </p>
              <ul class="list-disc list-inside space-y-2 ml-4">
                <li><strong>Cookies essentiels :</strong> Nécessaires au fonctionnement du site (panier, authentification)</li>
                <li><strong>Cookies analytiques :</strong> Nous aident à comprendre comment vous utilisez le site</li>
                <li><strong>Cookies de préférences :</strong> Mémorisent vos choix (langue, région)</li>
              </ul>
              <p>
                Vous pouvez configurer votre navigateur pour refuser les cookies. Cependant, certaines 
                fonctionnalités du site pourraient ne pas fonctionner correctement.
              </p>
            </div>
          </section>

          <!-- Limitation de responsabilité -->
          <section class="bg-white rounded-lg shadow-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              6. Limitation de responsabilité
            </h2>
            <div class="space-y-4 text-gray-700">
              <p>
                Ets La Lumière s'efforce de fournir des informations aussi précises que possible sur ce site. 
                Cependant, elle ne peut garantir l'exactitude, la complétude ou l'actualité des informations 
                diffusées.
              </p>
              <p>
                Ets La Lumière ne pourra être tenue responsable des dommages directs ou indirects résultant 
                de l'utilisation de ce site ou d'informations obtenues sur celui-ci.
              </p>
              <p>
                Les prix affichés sur le site sont donnés à titre indicatif et peuvent être modifiés sans 
                préavis. Le prix final applicable est celui affiché au moment de la validation de la commande.
              </p>
            </div>
          </section>

          <!-- Droit applicable -->
          <section class="bg-white rounded-lg shadow-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">
              7. Droit applicable et juridiction
            </h2>
            <div class="space-y-4 text-gray-700">
              <p>
                Les présentes mentions légales sont soumises au droit de la République Démocratique du Congo.
              </p>
              <p>
                En cas de litige, et à défaut de résolution amiable, les tribunaux de Kinshasa seront seuls 
                compétents.
              </p>
            </div>
          </section>

          <!-- Contact -->
          <section class="bg-orange-50 rounded-lg p-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">
              8. Contact
            </h2>
            <p class="text-gray-700 mb-4">
              Pour toute question concernant ces mentions légales, vous pouvez nous contacter :
            </p>
            <div class="text-gray-700 space-y-2">
              <p>📧 Email : <a href="mailto:legal@etslumiere.cd" class="text-orange-500 hover:underline">legal@etslumiere.cd</a></p>
              <p>📞 Téléphone : <a href="tel:+243812345678" class="text-orange-500 hover:underline">+243 81 234 56 78</a></p>
              <p>📍 Adresse : 123 Avenue de l'Indépendance, Kinshasa, RDC</p>
            </div>
          </section>

          <!-- Date de mise à jour -->
          <div class="text-center text-gray-500 text-sm">
            <p>Dernière mise à jour : {{ new Date().toLocaleDateString('fr-FR') }}</p>
          </div>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
// Meta tags pour SEO
useHead({
  title: 'Mentions Légales - Ets La Lumière',
  meta: [
    { name: 'description', content: 'Mentions légales de Ets La Lumière. Informations juridiques, propriété intellectuelle, protection des données, cookies.' }
  ]
})
</script>