<template>
  <header class="bg-white shadow-md sticky top-0 z-50">
    <div class="container mx-auto px-4 py-4">
      <div class="flex items-center justify-between">
        <!-- Logo -->
        <NuxtLink to="/" class="flex items-center space-x-2">
          <div class="text-2xl font-bold text-orange-600">
            Ets La Lumière
          </div>
        </NuxtLink>

        <!-- Search Bar -->
        <div class="flex-1 max-w-2xl mx-8">
          <form @submit.prevent="search" class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Rechercher des produits..."
              class="w-full px-4 py-2 pl-10 pr-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <svg
              class="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </form>
        </div>

        <!-- Cart Icon -->
        <NuxtLink to="/panier" class="relative p-2">
          <svg
            class="h-6 w-6 text-gray-700"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <span
            v-if="cartTotalItems > 0"
            class="absolute -top-1 -right-1 bg-orange-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center"
          >
            {{ cartTotalItems }}
          </span>
        </NuxtLink>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
const cartStore = useCartStore()
const router = useRouter()

const searchQuery = ref('')

const cartTotalItems = computed(() => cartStore.totalItems)

const search = () => {
  if (searchQuery.value.trim()) {
    router.push(`/recherche?q=${encodeURIComponent(searchQuery.value.trim())}`)
  }
}
</script>