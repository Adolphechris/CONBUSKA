/**
 * Composable pour ajouter des données structurées JSON-LD
 * Améliore le SEO avec des Rich Results Google
 */

export const useJsonLd = () => {
  /**
   * Ajoute le JSON-LD pour un produit
   */
  const addProductJsonLd = (article: any, prix: number, devise: string) => {
    const config = useRuntimeConfig()
    
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: article.nom,
      description: article.description || '',
      image: article.image_url,
      offers: {
        '@type': 'Offer',
        price: prix,
        priceCurrency: devise,
        availability: article.stock_disponible > 0 
          ? 'https://schema.org/InStock' 
          : 'https://schema.org/OutOfStock'
      }
    }
    
    useHead({
      script: [
        {
          type: 'application/ld+json',
          children: JSON.stringify(jsonLd)
        }
      ]
    })
  }
  
  /**
   * Ajoute le JSON-LD pour l'organisation
   */
  const addOrganizationJsonLd = () => {
    const config = useRuntimeConfig()
    
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: 'Ets La Lumière',
      url: config.public.siteUrl,
      logo: `${config.public.siteUrl}/logo.png`
    }
    
    useHead({
      script: [
        {
          type: 'application/ld+json',
          children: JSON.stringify(jsonLd)
        }
      ]
    })
  }
  
  /**
   * Ajoute le JSON-LD pour une page catégorie
   */
  const addItemListJsonLd = (items: any[], titre: string) => {
    const config = useRuntimeConfig()
    
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: titre,
      itemListElement: items.map((item, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        url: `${config.public.siteUrl}/produit/${item.code_article}`
      }))
    }
    
    useHead({
      script: [
        {
          type: 'application/ld+json',
          children: JSON.stringify(jsonLd)
        }
      ]
    })
  }
  
  return {
    addProductJsonLd,
    addOrganizationJsonLd,
    addItemListJsonLd
  }
}