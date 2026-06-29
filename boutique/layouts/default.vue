<template>
  <div class="min-h-screen flex flex-col">
    <AppHeader />
    
    <main class="flex-1">
      <slot />
    </main>
    
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
// PWA: Lier le manifest
useHead({
  link: [
    { rel: 'manifest', href: '/manifest.json' },
    { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
  ]
})

// PWA: Enregistrer le Service Worker
onMounted(() => {
  if (process.client && 'serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered:', registration.scope)
      })
      .catch((error) => {
        console.log('SW registration failed:', error)
      })
  }
})

// Initialize cart on mount
onMounted(() => {
  const cartStore = useCartStore()
  cartStore.initCart()
})
</script>
