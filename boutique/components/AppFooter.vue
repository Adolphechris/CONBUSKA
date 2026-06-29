<template>
  <footer class="bg-gray-800 text-white mt-auto">
    <div class="container mx-auto px-4 py-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <!-- Company Info -->
        <div>
          <h3 class="text-xl font-bold mb-4">Ets La Lumière</h3>
          <p class="text-gray-300 mb-2">
            Votre boutique de confiance au Congo
          </p>
          <p class="text-gray-300 text-sm">
            Livraison partout au Congo
          </p>
        </div>

        <!-- Contact -->
        <div>
          <h3 class="text-xl font-bold mb-4">Contact</h3>
          <p class="text-gray-300 mb-2">
            Email: contact@etslalumiere.cd
          </p>
          <p class="text-gray-300 mb-2">
            Téléphone: +242 XX XXX XXXX
          </p>
          <p class="text-gray-300 text-sm">
            Kinshasa, République Démocratique du Congo
          </p>
        </div>

        <!-- Legal Links -->
        <div>
          <h3 class="text-xl font-bold mb-4">Informations</h3>
          <ul class="space-y-2">
            <li>
              <NuxtLink to="/mentions-legales" class="text-gray-300 hover:text-white transition-colors">
                Mentions légales
              </NuxtLink>
            </li>
            <li>
              <NuxtLink to="/conditions-utilisation" class="text-gray-300 hover:text-white transition-colors">
                Conditions d'utilisation
              </NuxtLink>
            </li>
            <li>
              <NuxtLink to="/politique-confidentialite" class="text-gray-300 hover:text-white transition-colors">
                Politique de confidentialité
              </NuxtLink>
            </li>
          </ul>
        </div>
      </div>

      <div class="border-t border-gray-700 mt-8 pt-6 text-center text-gray-400 text-sm">
        <p>&copy; {{ currentYear }} Ets La Lumière. Tous droits réservés.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
const currentYear = computed(() => new Date().getFullYear())
</script>