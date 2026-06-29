import { defineStore } from 'pinia'

export interface PanierItem {
  code_article: string
  nom: string
  prix_unitaire: number
  quantite: number
  image_url: string
}

export const useCartStore = defineStore('cart', () => {
  // State
  const items = ref<PanierItem[]>([])

  // Getters
  const totalItems = computed(() => {
    return items.value.reduce((total, item) => total + item.quantite, 0)
  })
  
  const totalPrice = computed(() => {
    return items.value.reduce((total, item) => total + (item.prix_unitaire * item.quantite), 0)
  })

  const isEmpty = computed(() => {
    return items.value.length === 0
  })

  // Actions
  function initCart() {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('conbuska_cart')
      if (saved) {
        try {
          items.value = JSON.parse(saved)
        } catch (e) {
          items.value = []
        }
      }
    }
  }

  function saveCart() {
    if (typeof window !== 'undefined') {
      localStorage.setItem('conbuska_cart', JSON.stringify(items.value))
    }
  }

  function addItem(item: PanierItem) {
    const existing = items.value.find(i => i.code_article === item.code_article)
    
    if (existing) {
      existing.quantite += item.quantite
    } else {
      items.value.push(item)
    }
    
    saveCart()
  }

  function updateQuantity(code_article: string, quantite: number) {
    const item = items.value.find(i => i.code_article === code_article)
    
    if (item && quantite >= 1) {
      item.quantite = quantite
      saveCart()
    }
  }

  function removeItem(code_article: string) {
    items.value = items.value.filter(i => i.code_article !== code_article)
    saveCart()
  }

  function clearCart() {
    items.value = []
    saveCart()
  }

  function getItem(code_article: string) {
    return items.value.find(i => i.code_article === code_article)
  }

  return {
    items,
    totalItems,
    totalPrice,
    isEmpty,
    initCart,
    addItem,
    updateQuantity,
    removeItem,
    clearCart,
    getItem
  }
})