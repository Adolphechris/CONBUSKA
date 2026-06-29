import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ProductCard from '~/components/ProductCard.vue'

describe('ProductCard', () => {
  const mockArticle = {
    code_article: 'TEST001',
    nom: 'Produit Test',
    categorie: 'Test',
    prix: 10000,
    stock_disponible: 10,
    image_url: '/test.jpg',
    seuil_alerte: 5
  }

  it('affiche le nom du produit', () => {
    const wrapper = mount(ProductCard, {
      props: { article: mockArticle }
    })
    
    expect(wrapper.text()).toContain('Produit Test')
  })
  
  it('affiche le prix formaté', () => {
    const wrapper = mount(ProductCard, {
      props: { article: mockArticle }
    })
    
    expect(wrapper.text()).toContain('10 000')
  })

  it('désactive le bouton si stock = 0', () => {
    const articleOutOfStock = {
      ...mockArticle,
      stock_disponible: 0
    }
    
    const wrapper = mount(ProductCard, {
      props: { article: articleOutOfStock }
    })
    
    const button = wrapper.find('button')
    expect(button.attributes('disabled')).toBeDefined()
    expect(button.text()).toContain('Rupture de stock')
  })

  it('active le bouton si stock > 0', () => {
    const wrapper = mount(ProductCard, {
      props: { article: mockArticle }
    })
    
    const button = wrapper.find('button')
    expect(button.attributes('disabled')).toBeUndefined()
    expect(button.text()).toContain('Ajouter au panier')
  })

  it('contient un lien vers la fiche produit', () => {
    const wrapper = mount(ProductCard, {
      props: { article: mockArticle }
    })
    
    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe(`/produit/${mockArticle.code_article}`)
  })
})