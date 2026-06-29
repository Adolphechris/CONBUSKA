export interface Article {
  code_article: string
  nom: string
  categorie: string
  prix: number
  stock_disponible: number
  image_url: string
  description?: string
  seuil_alerte: number
  date_mise_a_jour?: Date
}

export interface LigneCommande {
  code_article: string
  quantite: number
  prix_unitaire: number
  nom_article: string
}

export interface Commande {
  id?: string
  date_commande: Date
  client: {
    nom: string
    email: string
    telephone?: string
    adresse?: string
  }
  lignes: LigneCommande[]
  total: number
  statut: string
  numero_facture?: string
  message_erreur?: string
}

export interface PanierItem {
  code_article: string
  nom: string
  prix_unitaire: number
  quantite: number
  image_url: string
}

export interface Categorie {
  nom: string
  count: number
}