<template>
  <div class="py-8 bg-gray-50">
    <div class="container mx-auto px-4 max-w-4xl">
      <h1 class="text-3xl font-bold text-gray-800 mb-8">Conditions d'utilisation</h1>

      <div class="bg-white rounded-lg shadow-md p-8 space-y-6">
        <section>
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">1. Acceptation des conditions</h2>
          <p class="text-gray-700 leading-relaxed">
            En accédant et en utilisant ce site web, vous acceptez d'être lié par ces conditions d'utilisation. 
            Si vous n'acceptez pas ces conditions, veuillez ne pas utiliser ce site.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">2. Description du service</h2>
          <p class="text-gray-700 leading-relaxed">
            Ets La Lumière est une boutique en ligne spécialisée dans la vente de produits électriques et électroniques 
            au Congo. Nous proposons une large gamme de produits incluant des luminaires, ampoules LED, panneaux solaires, 
            générateurs et accessoires divers.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">3. Commandes et paiements</h2>
          <p class="text-gray-700 leading-relaxed mb-3">
            Toutes les commandes passées sur ce site sont soumises à acceptation. Nous nous réservons le droit de 
            refuser ou d'annuler toute commande pour quelque raison que ce soit.
          </p>
          <p class="text-gray-700 leading-relaxed">
            Les prix sont affichés en USD et peuvent être modifiés sans préavis. Le paiement s'effectue à la livraison 
            ou selon les modalités convenues par email.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">4. Livraison</h2>
          <p class="text-gray-700 leading-relaxed">
            Nous livrons partout au Congo. Les délais de livraison varient selon votre localisation. 
            Les frais de livraison sont calculés et affichés avant la confirmation de votre commande.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">5. Retours et remboursements</h2>
          <p class="text-gray-700 leading-relaxed">
            Les retours sont acceptés dans un délai de 7 jours après réception, sous réserve que les produits 
            soient dans leur état d'origine. Les remboursements sont effectués selon notre politique de remboursement.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">6. Propriété intellectuelle</h2>
          <p class="text-gray-700 leading-relaxed">
            Tout le contenu de ce site, incluant textes, images, logos et designs, est la propriété exclusive 
            d'Ets La Lumière et est protégé par les lois sur la propriété intellectuelle.
          </p>
        </section>

        <section>
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">7. Contact</h2>
          <p class="text-gray-700 leading-relaxed">
            Pour toute question concernant ces conditions d'utilisation, veuillez nous contacter à :
          </p>
          <p class="text-gray-700 mt-2">
            📧 Email : contact@etslumiere.cd<br>
            📞 Téléphone : +243 XXX XXX XXX
          </p>
        </section>

        <section class="border-t pt-6">
          <p class="text-sm text-gray-600">
            Dernière mise à jour : {{ new Date().toLocaleDateString('fr-FR') }}
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// SEO
useHead({
  title: 'Conditions d\'utilisation - Ets La Lumière',
  meta: [
    { name: 'description', content: 'Conditions d\'utilisation de la boutique en ligne Ets La Lumière.' }
  ]
})
</script>