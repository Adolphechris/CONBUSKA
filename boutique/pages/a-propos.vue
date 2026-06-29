<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    
    <main class="py-12">
      <div class="container mx-auto px-4">
        <!-- Hero Section -->
        <div class="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 md:p-12 mb-12 text-white">
          <h1 class="text-4xl md:text-5xl font-bold mb-4">
            À propos de Ets La Lumière
          </h1>
          <p class="text-xl md:text-2xl opacity-90">
            Votre partenaire de confiance pour l'éclairage professionnel
          </p>
        </div>

        <!-- Notre Histoire -->
        <section class="mb-16">
          <div class="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 class="text-3xl font-bold text-gray-800 mb-4">
                Notre Histoire
              </h2>
              <p class="text-gray-600 mb-4">
                Fondée en 2010, <strong>Ets La Lumière</strong> est née d'une vision simple : 
                fournir à nos clients des solutions d'éclairage de qualité supérieure à des prix 
                accessibles.
              </p>
              <p class="text-gray-600 mb-4">
                Depuis plus de 15 ans, nous avons accompagné des milliers de professionnels 
                et particuliers dans leurs projets d'éclairage, en proposant une large gamme 
                de produits adaptés à tous les besoins.
              </p>
              <p class="text-gray-600">
                Aujourd'hui, nous sommes fiers de poursuivre cette mission en ligne, 
                en offrant une expérience d'achat moderne et pratique à travers notre 
                boutique en ligne.
              </p>
            </div>
            <div class="bg-white rounded-lg shadow-lg p-8">
              <div class="grid grid-cols-2 gap-6">
                <div class="text-center">
                  <div class="text-4xl font-bold text-orange-500 mb-2">15+</div>
                  <div class="text-gray-600">Années d'expérience</div>
                </div>
                <div class="text-center">
                  <div class="text-4xl font-bold text-orange-500 mb-2">5000+</div>
                  <div class="text-gray-600">Clients satisfaits</div>
                </div>
                <div class="text-center">
                  <div class="text-4xl font-bold text-orange-500 mb-2">10000+</div>
                  <div class="text-gray-600">Produits disponibles</div>
                </div>
                <div class="text-center">
                  <div class="text-4xl font-bold text-orange-500 mb-2">24/7</div>
                  <div class="text-gray-600">Support client</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Nos Valeurs -->
        <section class="mb-16">
          <h2 class="text-3xl font-bold text-gray-800 mb-8 text-center">
            Nos Valeurs
          </h2>
          <div class="grid md:grid-cols-3 gap-8">
            <div class="bg-white rounded-lg shadow-md p-6 text-center">
              <div class="text-5xl mb-4">🎯</div>
              <h3 class="text-xl font-bold text-gray-800 mb-3">Qualité</h3>
              <p class="text-gray-600">
                Nous sélectionnons rigoureusement chaque produit pour garantir 
                la meilleure qualité à nos clients.
              </p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6 text-center">
              <div class="text-5xl mb-4">🤝</div>
              <h3 class="text-xl font-bold text-gray-800 mb-3">Confiance</h3>
              <p class="text-gray-600">
                Une relation de confiance durable avec chacun de nos clients, 
                basée sur la transparence et le respect.
              </p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6 text-center">
              <div class="text-5xl mb-4">💡</div>
              <h3 class="text-xl font-bold text-gray-800 mb-3">Innovation</h3>
              <p class="text-gray-600">
                Nous restons à la pointe des dernières technologies d'éclairage 
                pour vous proposer les meilleures solutions.
              </p>
            </div>
          </div>
        </section>

        <!-- Notre Équipe -->
        <section class="mb-16">
          <h2 class="text-3xl font-bold text-gray-800 mb-8 text-center">
            Notre Équipe
          </h2>
          <p class="text-center text-gray-600 max-w-3xl mx-auto mb-8">
            Une équipe passionnée et expérimentée, dédiée à vous offrir le meilleur 
            service possible. Du conseil personnalisé à la livraison, nous sommes 
            à vos côtés à chaque étape.
          </p>
          <div class="grid md:grid-cols-4 gap-6">
            <div class="bg-white rounded-lg shadow-md p-6 text-center">
              <div class="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl">
                👨‍💼
              </div>
              <h3 class="font-bold text-gray-800">Directeur Général</h3>
              <p class="text-sm text-gray-600">Vision stratégique</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6 text-center">
              <div class="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl">
                👩‍💼
              </div>
              <h3 class="font-bold text-gray-800">Responsable Commercial</h3>
              <p class="text-sm text-gray-600">Relation client</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6 text-center">
              <div class="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl">
                👨‍🔧
              </div>
              <h3 class="font-bold text-gray-800">Expert Technique</h3>
              <p class="text-sm text-gray-600">Conseils produits</p>
            </div>
            <div class="bg-white rounded-lg shadow-md p-6 text-center">
              <div class="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl">
                👩‍💻
              </div>
              <h3 class="font-bold text-gray-800">Support Client</h3>
              <p class="text-sm text-gray-600">Assistance 24/7</p>
            </div>
          </div>
        </section>

        <!-- Notre Engagement -->
        <section class="bg-orange-50 rounded-2xl p-8 md:p-12">
          <h2 class="text-3xl font-bold text-gray-800 mb-6 text-center">
            Notre Engagement
          </h2>
          <div class="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div class="flex items-start">
              <span class="text-2xl mr-4">✓</span>
              <div>
                <h3 class="font-bold text-gray-800 mb-1">Produits de Qualité</h3>
                <p class="text-gray-600">Sélection rigoureuse de marques reconnues</p>
              </div>
            </div>
            <div class="flex items-start">
              <span class="text-2xl mr-4">✓</span>
              <div>
                <h3 class="font-bold text-gray-800 mb-1">Prix Compétitifs</h3>
                <p class="text-gray-600">Meilleurs prix du marché garantis</p>
              </div>
            </div>
            <div class="flex items-start">
              <span class="text-2xl mr-4">✓</span>
              <div>
                <h3 class="font-bold text-gray-800 mb-1">Livraison Rapide</h3>
                <p class="text-gray-600">24-48h à Kinshasa, partout au Congo</p>
              </div>
            </div>
            <div class="flex items-start">
              <span class="text-2xl mr-4">✓</span>
              <div>
                <h3 class="font-bold text-gray-800 mb-1">Service Client</h3>
                <p class="text-gray-600">Accompagnement personnalisé</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
// Meta tags pour SEO
useHead({
  title: 'À propos - Ets La Lumière',
  meta: [
    { name: 'description', content: 'Découvrez l\'histoire de Ets La Lumière, votre partenaire de confiance pour l\'éclairage professionnel au Congo.' }
  ]
})
</script>