import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCartStore } from '~/stores/cart'

describe('Cart Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('ajoute un article au panier', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Produit Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    expect(cart.items.length).toBe(1)
    expect(cart.totalItems).toBe(1)
    expect(cart.totalPrice).toBe(1000)
  })

  it('incrémente la quantité si article existe', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Produit Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Produit Test',
      prix_unitaire: 1000,
      quantite: 2,
      image_url: '/test.jpg'
    })
    
    expect(cart.items.length).toBe(1)
    expect(cart.items[0].quantite).toBe(3)
    expect(cart.totalItems).toBe(3)
  })

  it('supprime un article du panier', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Produit Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    cart.removeItem('TEST001')
    
    expect(cart.items.length).toBe(0)
    expect(cart.isEmpty).toBe(true)
  })

  it('met à jour la quantité', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Produit Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    cart.updateQuantity('TEST001', 5)
    
    expect(cart.items[0].quantite).toBe(5)
    expect(cart.totalItems).toBe(5)
    expect(cart.totalPrice).toBe(5000)
  })

  it('ne met pas à jour si quantité < 1', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Produit Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    cart.updateQuantity('TEST001', 0)
    
    expect(cart.items[0].quantite).toBe(1)
  })

  it('vide le panier', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Produit Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    cart.addItem({
      code_article: 'TEST002',
      nom: 'Produit Test 2',
      prix_unitaire: 2000,
      quantite: 2,
      image_url: '/test2.jpg'
    })
    
    cart.clearCart()
    
    expect(cart.items.length).toBe(0)
    expect(cart.isEmpty).toBe(true)
    expect(cart.totalItems).toBe(0)
    expect(cart.totalPrice).toBe(0)
  })

  it('récupère un article par code', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Produit Test',
      prix_unitaire: 1000,
      quantite: 1,
      image_url: '/test.jpg'
    })
    
    const item = cart.getItem('TEST001')
    
    expect(item).toBeDefined()
    expect(item?.nom).toBe('Produit Test')
    expect(item?.quantite).toBe(1)
  })

  it('calcule correctement le total avec plusieurs articles', () => {
    const cart = useCartStore()
    
    cart.addItem({
      code_article: 'TEST001',
      nom: 'Produit 1',
      prix_unitaire: 1000,
      quantite: 2,
      image_url: '/test1.jpg'
    })
    
    cart.addItem({
      code_article: 'TEST002',
      nom: 'Produit 2',
      prix_unitaire: 2000,
      quantite: 3,
      image_url: '/test2.jpg'
    })
    
    expect(cart.totalItems).toBe(5)
    expect(cart.totalPrice).toBe(8000) // (2 * 1000) + (3 * 2000)
  })
})