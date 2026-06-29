import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BadgeStock from '~/components/BadgeStock.vue'

describe('BadgeStock', () => {
  it('affiche "En stock" en vert quand stock > seuil', () => {
    const wrapper = mount(BadgeStock, {
      props: {
        stock_disponible: 10,
        seuil_alerte: 5
      }
    })
    
    expect(wrapper.text()).toContain('En stock')
    expect(wrapper.find('span').classes()).toContain('bg-green')
  })

  it('affiche "Plus que X en stock" en orange quand stock <= seuil et > 0', () => {
    const wrapper = mount(BadgeStock, {
      props: {
        stock_disponible: 3,
        seuil_alerte: 5
      }
    })
    
    expect(wrapper.text()).toContain('Plus que 3 en stock')
    expect(wrapper.find('span').classes()).toContain('bg-orange')
  })

  it('affiche "Rupture de stock" en rouge quand stock = 0', () => {
    const wrapper = mount(BadgeStock, {
      props: {
        stock_disponible: 0,
        seuil_alerte: 5
      }
    })
    
    expect(wrapper.text()).toContain('Rupture de stock')
    expect(wrapper.find('span').classes()).toContain('bg-red')
  })

  it('gère le cas stock = seuil exact', () => {
    const wrapper = mount(BadgeStock, {
      props: {
        stock_disponible: 5,
        seuil_alerte: 5
      }
    })
    
    expect(wrapper.text()).toContain('Plus que 5 en stock')
    expect(wrapper.find('span').classes()).toContain('bg-orange')
  })
})