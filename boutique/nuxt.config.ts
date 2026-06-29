// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },

  // Modules
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt'
  ],

  // TypeScript
  typescript: {
    strict: true
  },

  // Runtime configuration (public variables for the client)
  runtimeConfig: {
    public: {
      firebaseApiKey: process.env.VITE_FIREBASE_API_KEY || '',
      firebaseAuthDomain: process.env.VITE_FIREBASE_AUTH_DOMAIN || '',
      firebaseProjectId: process.env.VITE_FIREBASE_PROJECT_ID || '',
      firebaseStorageBucket: process.env.VITE_FIREBASE_STORAGE_BUCKET || '',
      firebaseMessagingSenderId: process.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
      firebaseAppId: process.env.VITE_FIREBASE_APP_ID || '',
      imageDefautUrl: process.env.VITE_IMAGE_DEFAUT_URL || '/images/default-product.jpg',
      siteUrl: process.env.VITE_SITE_URL || 'https://boutique.conbuska.cd',
      appName: process.env.VITE_APP_NAME || 'Ets La Lumière',
      currency: process.env.VITE_CURRENCY || 'CDF',
    }
  },

  // App configuration
  app: {
    head: {
      title: 'Ets La Lumière',
      titleTemplate: '%s - Ets La Lumière',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Boutique en ligne Ets La Lumière - Achetez vos produits préférés au Congo' },
        { name: 'theme-color', content: '#ea580c' },
        // Open Graph
        { property: 'og:title', content: 'Ets La Lumière - Éclairage Professionnel RDC' },
        { property: 'og:description', content: 'Boutique en ligne leader en RDC. +10 000 produits, livraison gratuite, paiement à la livraison.' },
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: 'Ets La Lumière' },
        { property: 'og:locale', content: 'fr_CD' },
        // Twitter
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:title', content: 'Ets La Lumière - Éclairage Professionnel RDC' },
        { name: 'twitter:description', content: 'Boutique en ligne leader en RDC. +10 000 produits, livraison gratuite.' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'canonical', href: process.env.VITE_SITE_URL || 'https://boutique.conbuska.cd' },
        { rel: 'manifest', href: '/manifest.json' },
      ],
      htmlAttrs: {
        lang: 'fr',
      },
    },
    // PWA configuration via service worker
    pageTransition: {
      name: 'page',
      mode: 'out-in'
    },
  },

  // CSS global
  css: [
    '~/assets/css/main.css',
  ],

  // Nitro Configuration (production build)
  nitro: {
    preset: 'static',
    // Optimisation des assets
    compressPublicAssets: true,
    minify: true,
    // Inlining CSS critiques pour le FCP
    inlineDynamicImports: true,
    // Cache des assets statiques
    static: true,
    // Generation des routes statiques (prerender)
    prerender: {
      routes: [
        '/',
        '/a-propos',
        '/conditions-utilisation',
        '/contact',
        '/faq',
        '/livraison',
        '/mentions-legales',
        '/politique-confidentialite',
        '/panier',
        '/checkout',
        '/confirmation',
        '/categorie/tous',
      ],
      crawlLinks: true,
    },
  },

  // Build optimization
  build: {
    // Transpile si nécessaire
    transpile: ['firebase'],
  },

  // PostCSS/Tailwind optimization
  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },

  // Performance: generate SPA fallback for 404
  generate: {
    fallback: '404.html',
  },

  // Hooks for additional optimization
  hooks: {
    'build:done': () => {
      console.log('✅ Build terminé avec succès');
      console.log('📁 Les fichiers statiques sont dans .output/public/');
    },
  },
})
