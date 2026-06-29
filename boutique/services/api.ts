/**
 * Service API pour communiquer avec Django/Conbuska
 * Remplace Firebase pour la récupération des articles et la création de commandes
 */

const API_BASE = 'http://localhost:8000/api'

export interface Article {
  id: number
  code: string
  nom: string
  description: string
  categorie: number
  categorie_nom: string
  prix_vente: number
  prix_fc: number
  valeur_usd: number
  image_url: string | null
  est_publie: boolean
  stock_dispo: number
}

export interface Categorie {
  id: number
  nom: string
  description: string
}

export interface CommandeData {
  articles: Array<{
    code_article: string
    quantite: number
  }>
  client: {
    nom: string
    email?: string
    telephone: string
    adresse: string
    ville?: string
  }
}

export interface CommandeResult {
  success: boolean
  facture_id: number
  facture_code: string
  total_usd: number
  total_fc: number
  message: string
}

/**
 * Récupérer toutes les catégories
 */
export async function getCategories(): Promise<Categorie[]> {
  try {
    const response = await fetch(`${API_BASE}/categories/`)
    if (!response.ok) throw new Error('Erreur réseau')
    const data = await response.json()
    return data.results || data
  } catch (error) {
    console.error('Erreur getCategories:', error)
    return []
  }
}

/**
 * Récupérer tous les articles publiés
 */
export async function getArticles(): Promise<Article[]> {
  try {
    const response = await fetch(`${API_BASE}/articles/`)
    if (!response.ok) throw new Error('Erreur réseau')
    const data = await response.json()
    return data.results || data
  } catch (error) {
    console.error('Erreur getArticles:', error)
    return []
  }
}

/**
 * Récupérer les nouveautés (articles récents)
 */
export async function getNouveautes(): Promise<Article[]> {
  try {
    const response = await fetch(`${API_BASE}/articles/nouveautes/`)
    if (!response.ok) throw new Error('Erreur réseau')
    const data = await response.json()
    return data.results || data
  } catch (error) {
    console.error('Erreur getNouveautes:', error)
    return []
  }
}

/**
 * Récupérer les articles par catégorie
 */
export async function getArticlesParCategorie(categorie: string): Promise<Article[]> {
  try {
    const url = categorie === 'Tous' 
      ? `${API_BASE}/articles/`
      : `${API_BASE}/articles/par_categorie/?categorie=${encodeURIComponent(categorie)}`
    
    const response = await fetch(url)
    if (!response.ok) throw new Error('Erreur réseau')
    const data = await response.json()
    return data.results || data
  } catch (error) {
    console.error('Erreur getArticlesParCategorie:', error)
    return []
  }
}

/**
 * Rechercher des articles
 */
export async function rechercherArticles(query: string): Promise<Article[]> {
  try {
    const response = await fetch(`${API_BASE}/articles/recherche/?q=${encodeURIComponent(query)}`)
    if (!response.ok) throw new Error('Erreur réseau')
    const data = await response.json()
    return data.results || data
  } catch (error) {
    console.error('Erreur rechercherArticles:', error)
    return []
  }
}

/**
 * Créer une commande (facture)
 */
export async function creerCommande(data: CommandeData): Promise<CommandeResult> {
  try {
    const response = await fetch(`${API_BASE}/commandes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Erreur lors de la création de la commande')
    }

    return await response.json()
  } catch (error) {
    console.error('Erreur creerCommande:', error)
    throw error
  }
}