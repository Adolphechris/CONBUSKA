"""
Module d'import des commandes depuis Firestore vers Conbuska.

Ce module permet de:
- Récupérer les commandes depuis Firestore (statut "nouveau")
- Vérifier la disponibilité des articles et stocks
- Créer les factures dans Conbuska
- Décrémenter les stocks
- Mettre à jour le statut des commandes dans Firestore

Architecture:
- importer_commandes(): Fonction principale d'import
- traiter_commande(): Traitement d'une commande individuelle
- Vérifications métier (articles, stocks)
- Création client/facture
- Gestion erreurs et retry
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from decimal import Decimal

import firebase_admin
from firebase_admin import firestore

from django.db.models import Max
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from ecommerce.exceptions import (
    FirebaseConnectionError,
    SyncError,
)
from ecommerce.sync.services import FirestoreSyncService
from produits.models import Article, Magasin
from produits.services import StockService
from factures.models import Facture, DetailsFacture, FactureClient
from factures.services.facture_service import FactureService
from clients.models import Client

logger = logging.getLogger('ecommerce.import')

# Constantes
MAX_RETRIES = 3
BACKOFF_DELAYS = [2, 4, 8]  # secondes

# Statistiques globales
_import_stats = {
    'dernier_import': None,
    'commandes_importees': 0,
    'commandes_en_erreur': 0,
    'dernieres_erreurs': [],
}


class ImportCommandesService:
    """
    Service d'import des commandes depuis Firestore vers Conbuska.
    
    Points d'entrée:
    - importer_commandes(): Import toutes les commandes "nouveau"
    - traiter_commande(): Traite une commande spécifique
    - get_import_stats(): Retourne les statistiques
    """
    
    @classmethod
    def importer_commandes(cls, limit: Optional[int] = None) -> Dict:
        """
        Importe toutes les commandes en statut "nouveau" depuis Firestore.
        
        Args:
            limit: Nombre maximum de commandes à traiter (None = toutes)
        
        Returns:
            Dict avec statistiques: {
                'succes': int,
                'erreurs': int,
                'details': List[Dict]
            }
        """
        logger.info("[IMPORT] Début de l'import des commandes")
        
        try:
            # Récupérer les commandes "nouveau"
            commandes = cls._recuperer_commandes_nouveau(limit)
            
            if not commandes:
                logger.info("[IMPORT] Aucune commande à importer")
                return {'succes': 0, 'erreurs': 0, 'details': []}
            
            logger.info(f"[IMPORT] {len(commandes)} commande(s) à traiter")
            
            succes = 0
            erreurs = 0
            details = []
            
            # Traiter chaque commande séquentiellement
            for doc_id, data in commandes.items():
                try:
                    resultat = cls.traiter_commande(doc_id, data)
                    if resultat['succes']:
                        succes += 1
                    else:
                        erreurs += 1
                    details.append(resultat)
                    
                except Exception as e:
                    erreurs += 1
                    error_msg = f"Erreur traitement commande {doc_id}: {e}"
                    logger.error(f"[IMPORT] {error_msg}")
                    details.append({
                        'doc_id': doc_id,
                        'succes': False,
                        'erreur': error_msg
                    })
                    cls._add_error(error_msg)
            
            # Mettre à jour les statistiques
            _import_stats['dernier_import'] = timezone.now()
            _import_stats['commandes_importees'] += succes
            _import_stats['commandes_en_erreur'] += erreurs
            
            logger.info(
                f"[IMPORT] Import terminé: {succes} succès, {erreurs} erreurs"
            )
            
            return {
                'succes': succes,
                'erreurs': erreurs,
                'details': details
            }
            
        except Exception as e:
            error_msg = f"Erreur fatale lors de l'import: {e}"
            logger.error(f"[IMPORT] {error_msg}", exc_info=True)
            raise FirebaseConnectionError(error_msg) from e
    
    @classmethod
    def traiter_commande(cls, doc_id: str, data: Dict) -> Dict:
        """
        Traite une commande individuelle.
        
        Args:
            doc_id: ID du document Firestore
            data: Données de la commande
        
        Returns:
            Dict avec résultat du traitement
        """
        logger.info(f"[IMPORT] Traitement commande {doc_id}")
        
        try:
            # 1. Vérifier les articles
            validation_articles = cls._verifier_articles(data.get('lignes', []))
            if not validation_articles['valide']:
                cls._marquer_erreur(doc_id, validation_articles['erreur'])
                return {
                    'doc_id': doc_id,
                    'succes': False,
                    'erreur': validation_articles['erreur']
                }
            
            # 2. Vérifier les stocks
            validation_stocks = cls._verifier_stocks(data.get('lignes', []))
            if not validation_stocks['valide']:
                cls._marquer_erreur(doc_id, validation_stocks['erreur'])
                return {
                    'doc_id': doc_id,
                    'succes': False,
                    'erreur': validation_stocks['erreur']
                }
            
            # 3. Créer ou trouver le client
            client = cls._creer_ou_trouver_client(data.get('client', {}))
            if not client:
                erreur = "Erreur création client"
                cls._marquer_erreur(doc_id, erreur)
                return {
                    'doc_id': doc_id,
                    'succes': False,
                    'erreur': erreur
                }
            
            # 4. Créer la facture (transaction atomique)
            facture = cls._creer_facture(client, data)
            if not facture:
                erreur = "Erreur création facture"
                cls._marquer_erreur(doc_id, erreur)
                return {
                    'doc_id': doc_id,
                    'succes': False,
                    'erreur': erreur
                }
            
            # 5. Mettre à jour Firestore (succès)
            cls._mettre_a_jour_succes(doc_id, facture.numero)
            
            # 6. Repousser les stocks vers Firestore
            cls._synchroniser_stocks_articles(data.get('lignes', []))
            
            logger.info(f"[IMPORT] Commande {doc_id} importée avec succès (facture #{facture.numero})")
            
            return {
                'doc_id': doc_id,
                'succes': True,
                'facture_numero': facture.numero,
                'client_nom': client.nom
            }
            
        except Exception as e:
            error_msg = f"Erreur traitement commande {doc_id}: {e}"
            logger.error(f"[IMPORT] {error_msg}", exc_info=True)
            cls._marquer_erreur(doc_id, str(e))
            cls._add_error(error_msg)
            return {
                'doc_id': doc_id,
                'succes': False,
                'erreur': str(e)
            }
    
    @staticmethod
    def _verifier_articles(lignes: List[Dict]) -> Dict:
        """
        Vérifie que tous les articles existent dans Conbuska.
        
        Args:
            lignes: Liste des lignes de commande
        
        Returns:
            Dict: {'valide': bool, 'erreur': str}
        """
        for ligne in lignes:
            code_article = ligne.get('code_article')
            if not code_article:
                return {
                    'valide': False,
                    'erreur': f"Code article manquant dans la ligne"
                }
            
            try:
                # Conversion string → int (Firestore stocke en string)
                code_int = int(code_article)
                if not Article.objects.filter(code=code_int).exists():
                    return {
                        'valide': False,
                        'erreur': f"Article inconnu : {code_article}"
                    }
            except (ValueError, TypeError):
                return {
                    'valide': False,
                    'erreur': f"Article inconnu : {code_article} (code invalide)"
                }
        
        return {'valide': True, 'erreur': ''}
    
    @staticmethod
    def _verifier_stocks(lignes: List[Dict]) -> Dict:
        """
        Vérifie que le stock est suffisant pour chaque article.
        
        Args:
            lignes: Liste des lignes de commande
        
        Returns:
            Dict: {'valide': bool, 'erreur': str}
        """
        try:
            magasin = Magasin.objects.get(is_principal=True)
        except Magasin.DoesNotExist:
            return {
                'valide': False,
                'erreur': "Aucun magasin principal configuré"
            }
        
        for ligne in lignes:
            code_article = ligne.get('code_article')
            quantite_demandee = ligne.get('quantite', 0)
            nom_article = ligne.get('nom_article', 'Inconnu')
            
            try:
                code_int = int(code_article)
                article = Article.objects.get(code=code_int)
                
                # Calculer le stock disponible
                stock_disponible = article.stock  # Propriété du modèle
                
                if stock_disponible < quantite_demandee:
                    return {
                        'valide': False,
                        'erreur': (
                            f"Stock insuffisant pour {nom_article} "
                            f"(demandé : {quantite_demandee}, disponible : {stock_disponible})"
                        )
                    }
                    
            except Article.DoesNotExist:
                return {
                    'valide': False,
                    'erreur': f"Article inconnu : {code_article}"
                }
        
        return {'valide': True, 'erreur': ''}
    
    @staticmethod
    def _creer_ou_trouver_client(client_data: Dict) -> Optional[Client]:
        """
        Crée un nouveau client ou trouve un client existant par email.
        
        Args:
            client_data: Dict avec nom, email, telephone, adresse
        
        Returns:
            Client instance ou None
        """
        email = client_data.get('email', '').strip().lower()
        
        if not email:
            logger.error("[IMPORT] Email client manquant")
            return None
        
        # Chercher par email
        try:
            return Client.objects.get(email__iexact=email)
        except Client.DoesNotExist:
            pass
        
        # Créer un nouveau client "maison"
        try:
            from django.db import transaction
            
            with transaction.atomic():
                # Générer un code unique
                dernier_code = Client.objects.aggregate(
                    max_code=Max('code')
                )['max_code'] or 3000
                nouveau_code = dernier_code + 1
                
                client = Client.objects.create(
                    code=nouveau_code,
                    nom=client_data.get('nom', 'Client en ligne').strip(),
                    email=email,
                    telephone=client_data.get('telephone', ''),
                    adresse=client_data.get('adresse', ''),
                    ville='Non spécifiée'
                )
                
                logger.info(f"[IMPORT] Nouveau client créé: {client.nom} (code: {client.code})")
                return client
                
        except Exception as e:
            logger.error(f"[IMPORT] Erreur création client: {e}")
            return None
    
    @staticmethod
    def _creer_facture(client: Client, commande_data: Dict) -> Optional[Facture]:
        """
        Crée une facture à partir des données de commande.
        
        Args:
            client: Instance Client
            commande_data: Dict avec toutes les données de commande
        
        Returns:
            Facture instance ou None
        """
        try:
            with transaction.atomic():
                # Récupérer l'utilisateur système pour l'import automatique
                User = get_user_model()
                user_systemique, _ = User.objects.get_or_create(
                    username='system_import',
                    defaults={'is_staff': True, 'is_superuser': True}
                )
                
                # Récupérer le taux USD
                from parametres.models import get_taux_usd_cdf
                taux_usd = get_taux_usd_cdf()
                
                # Créer la facture en mode DRAFT
                facture = Facture.objects.create(
                    client_comptoir=client.nom,
                    devise="FC",  # Devise principale Conbuska (max_length=2)
                    taux=taux_usd,
                    cree_par=user_systemique,
                    valide=False  # DRAFT
                )
                
                # Lier le client
                FactureClient.objects.create(
                    facture=facture,
                    client=client
                )
                
                # Ajouter les lignes d'articles
                for ligne in commande_data.get('lignes', []):
                    code_article = int(ligne['code_article'])
                    quantite = ligne['quantite']
                    prix_unitaire = Decimal(str(ligne['prix_unitaire']))
                    
                    article = Article.objects.get(code=code_article)
                    
                    # Utiliser le service de facturation
                    FactureService.ajouter_article_facture(
                        facture=facture,
                        article=article,
                        qte=quantite
                    )
                
                # Valider la facture (décrémente stocks, crée mouvements)
                FactureService.valider(
                    facture=facture,
                    user=user_systemique,
                    date_facture=commande_data.get('date_commande')
                )
                
                logger.info(
                    f"[IMPORT] Facture #{facture.numero} créée et validée "
                    f"pour client {client.nom}"
                )
                
                return facture
                
        except Exception as e:
            logger.error(f"[IMPORT] Erreur création facture: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _marquer_erreur(doc_id: str, message_erreur: str) -> None:
        """
        Marque une commande comme en erreur dans Firestore.
        
        Args:
            doc_id: ID du document Firestore
            message_erreur: Message d'erreur
        """
        try:
            def _update():
                db = FirestoreSyncService._get_firestore_client()
                db.collection('commandes_en_ligne').document(doc_id).update({
                    'statut': 'erreur',
                    'message_erreur': message_erreur,
                    'tentatives_import': firestore.Increment(1)
                })
            
            FirestoreSyncService._execute_with_retry(
                _update, f"marquer erreur commande {doc_id}"
            )
            
        except Exception as e:
            logger.error(
                f"[IMPORT] Erreur mise à jour statut commande {doc_id}: {e}"
            )
    
    @staticmethod
    def _mettre_a_jour_succes(doc_id: str, numero_facture: int) -> None:
        """
        Marque une commande comme traitée dans Firestore.
        
        Args:
            doc_id: ID du document Firestore
            numero_facture: Numéro de facture générée
        """
        try:
            def _update():
                db = FirestoreSyncService._get_firestore_client()
                db.collection('commandes_en_ligne').document(doc_id).update({
                    'statut': 'traite',
                    'numero_facture': numero_facture,
                    'tentatives_import': firestore.Increment(1)
                })
            
            FirestoreSyncService._execute_with_retry(
                _update, f"marquer succès commande {doc_id}"
            )
            
        except Exception as e:
            logger.error(
                f"[IMPORT] Erreur mise à jour statut commande {doc_id}: {e}"
            )
    
    @staticmethod
    def _synchroniser_stocks_articles(lignes: List[Dict]) -> None:
        """
        Repousse les stocks mis à jour vers Firestore.
        
        Args:
            lignes: Liste des lignes de commande
        """
        codes_articles = set()
        for ligne in lignes:
            try:
                code_int = int(ligne['code_article'])
                codes_articles.add(code_int)
            except (ValueError, TypeError):
                continue
        
        # Synchroniser chaque article impacté
        for code in codes_articles:
            try:
                article = Article.objects.get(code=code)
                if article.est_publie:
                    FirestoreSyncService.sync_article(article, force=True)
            except Article.DoesNotExist:
                continue
            except Exception as e:
                logger.warning(
                    f"[IMPORT] Erreur sync stock article {code}: {e}"
                )
    
    @staticmethod
    def _recuperer_commandes_nouveau(limit: Optional[int] = None) -> Dict:
        """
        Récupère les commandes en statut "nouveau" depuis Firestore.
        
        Args:
            limit: Limite de commandes à récupérer
        
        Returns:
            Dict: {doc_id: data}
        """
        def _fetch():
            db = FirestoreSyncService._get_firestore_client()
            query = db.collection('commandes_en_ligne').where('statut', '==', 'nouveau')
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            return {doc.id: doc.to_dict() for doc in docs}
        
        return FirestoreSyncService._execute_with_retry(
            _fetch, "récupération commandes nouveau"
        )
    
    @staticmethod
    def _add_error(error_msg: str) -> None:
        """Ajoute une erreur aux statistiques."""
        _import_stats['dernieres_erreurs'].append(
            f"[{timezone.now().isoformat()}] {error_msg}"
        )
        if len(_import_stats['dernieres_erreurs']) > 5:
            _import_stats['dernieres_erreurs'] = _import_stats['dernieres_erreurs'][-5:]
    
    @staticmethod
    def get_import_stats() -> Dict:
        """
        Retourne les statistiques d'import.
        
        Returns:
            Dict avec statistiques
        """
        return {
            'dernier_import': _import_stats['dernier_import'],
            'commandes_importees': _import_stats['commandes_importees'],
            'commandes_en_erreur': _import_stats['commandes_en_erreur'],
            'dernieres_erreurs': _import_stats['dernieres_erreurs'][-5:],
        }


