"""
dashboard/services.py

Services du dashboard avec cache Redis et mode offline.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.cache import cache
import json


class DashboardService:
    """
    Service principal du dashboard avec cache Redis.
    
    Fonctionnalités :
    - Cache des données fréquemment consultées
    - Mode offline avec données en cache
    - Statistiques en temps réel
    - Alertes intelligentes
    """
    
    CACHE_TIMEOUT = 300  # 5 minutes
    CACHE_KEY_PREFIX = 'dashboard'
    
    @classmethod
    def _get_cache_key(cls, key: str) -> str:
        """Génère une clé de cache avec préfixe."""
        return f"{cls.CACHE_KEY_PREFIX}:{key}"
    
    @classmethod
    def get_statistiques_generales(cls) -> Dict[str, Any]:
        """
        Récupère les statistiques générales avec cache.
        """
        cache_key = cls._get_cache_key('statistiques_generales')
        
        # Essayer de récupérer depuis le cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Calculer les statistiques
        from factures.models import Facture
        from commandes.models import Commande
        from caisse.models import MouvementCaisse
        from produits.models import Article
        from paie.models import Paie
        from clients.models import Client
        
        aujourd_hui = timezone.now().date()
        debut_mois = aujourd_hui.replace(day=1)
        debut_annee = aujourd_hui.replace(month=1, day=1)
        
        # Ventes du mois
        ventes_mois = Facture.objects.filter(
            date_facture__gte=debut_mois,
            actif=True
        ).aggregate(
            total=Sum('montant_total'),
            nombre=Count('id')
        )
        
        # Ventes de l'année
        ventes_annee = Facture.objects.filter(
            date_facture__gte=debut_annee,
            actif=True
        ).aggregate(
            total=Sum('montant_total'),
            nombre=Count('id')
        )
        
        # Commandes en cours
        commandes_en_cours = Commande.objects.filter(
            statut__in=[Commande.BROUILLON, Commande.VALIDEE],
            actif=True
        ).count()
        
        # Mouvements caisse du mois
        caisse_entrees = MouvementCaisse.objects.filter(
            date_mouvement__gte=debut_mois,
            type_mouvement='ENTREE'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        caisse_sorties = MouvementCaisse.objects.filter(
            date_mouvement__gte=debut_mois,
            type_mouvement='SORTIE'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Stock
        articles_total = Article.objects.filter(actif=True).count()
        articles_stock_bas = Article.objects.filter(
            actif=True,
            quantite_stock__lte=10
        ).count()
        articles_rupture = Article.objects.filter(
            actif=True,
            quantite_stock=0
        ).count()
        
        # Clients
        clients_total = Client.objects.filter(actif=True).count()
        clients_nouveaux = Client.objects.filter(
            date_creation__gte=debut_mois,
            actif=True
        ).count()
        
        # Paie du mois
        paie_mois = Paie.objects.filter(
            mois=debut_mois,
            valide=True
        ).aggregate(
            total=Sum('net_a_payer'),
            nombre=Count('id')
        )
        
        statistiques = {
            'ventes': {
                'mois': {
                    'total': float(ventes_mois['total'] or 0),
                    'nombre': ventes_mois['nombre'] or 0,
                },
                'annee': {
                    'total': float(ventes_annee['total'] or 0),
                    'nombre': ventes_annee['nombre'] or 0,
                },
            },
            'commandes': {
                'en_cours': commandes_en_cours,
            },
            'caisse': {
                'entrees_mois': float(caisse_entrees),
                'sorties_mois': float(caisse_sorties),
                'solde_mois': float(caisse_entrees - caisse_sorties),
            },
            'stock': {
                'total_articles': articles_total,
                'stock_bas': articles_stock_bas,
                'rupture': articles_rupture,
            },
            'clients': {
                'total': clients_total,
                'nouveaux_mois': clients_nouveaux,
            },
            'paie': {
                'mois': {
                    'total': float(paie_mois['total'] or 0),
                    'nombre': paie_mois['nombre'] or 0,
                },
            },
            'timestamp': timezone.now().isoformat(),
        }
        
        # Mettre en cache
        cache.set(cache_key, statistiques, cls.CACHE_TIMEOUT)
        
        return statistiques
    
    @classmethod
    def get_activites_recentes(cls, limite: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère les activités récentes avec cache.
        """
        cache_key = cls._get_cache_key(f'activites_recentes:{limite}')
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        activites = []
        
        # Dernières factures
        from factures.models import Facture
        for facture in Facture.objects.filter(actif=True).order_by('-date_facture')[:5]:
            activites.append({
                'type': 'facture',
                'icon': 'fa fa-file-text',
                'color': 'primary',
                'title': f"Facture #{facture.numero}",
                'description': f"{facture.client.nom} - {facture.montant_total:,.0f} FC",
                'date': facture.date_facture,
                'url': f'/factures/{facture.pk}',
            })
        
        # Dernières commandes
        from commandes.models import Commande
        for commande in Commande.objects.filter(actif=True).order_by('-date_commande')[:5]:
            activites.append({
                'type': 'commande',
                'icon': 'fa fa-shopping-cart',
                'color': 'warning',
                'title': f"Commande #{commande.numero}",
                'description': f"{commande.fournisseur.nom}",
                'date': commande.date_commande,
                'url': f'/commandes/commande/{commande.pk}',
            })
        
        # Derniers mouvements caisse
        from caisse.models import MouvementCaisse
        for mouvement in MouvementCaisse.objects.order_by('-date_mouvement')[:5]:
            type_mouvement = 'Entrée' if mouvement.type_mouvement == 'ENTREE' else 'Sortie'
            activites.append({
                'type': 'caisse',
                'icon': 'fa fa-money',
                'color': 'success' if mouvement.type_mouvement == 'ENTREE' else 'danger',
                'title': f"{type_mouvement} caisse",
                'description': f"{mouvement.montant:,.0f} FC - {mouvement.rubrique.nom}",
                'date': mouvement.date_mouvement,
                'url': f'/caisse',
            })
        
        # Trier par date
        activites.sort(key=lambda x: x['date'], reverse=True)
        activites = activites[:limite]
        
        # Mettre en cache
        cache.set(cache_key, activites, cls.CACHE_TIMEOUT)
        
        return activites
    
    @classmethod
    def get_alertes(cls) -> List[Dict[str, Any]]:
        """
        Récupère les alertes importantes.
        """
        cache_key = cls._get_cache_key('alertes')
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        alertes = []
        
        # Alertes stock
        from produits.models import Article
        articles_rupture = Article.objects.filter(actif=True, quantite_stock=0)
        for article in articles_rupture[:5]:
            alertes.append({
                'type': 'danger',
                'icon': 'fa fa-exclamation-triangle',
                'title': 'Rupture de stock',
                'message': f"{article.designation} est en rupture",
                'url': f'/produits/article/{article.pk}',
            })
        
        articles_stock_bas = Article.objects.filter(
            actif=True,
            quantite_stock__gt=0,
            quantite_stock__lte=10
        )
        for article in articles_stock_bas[:3]:
            alertes.append({
                'type': 'warning',
                'icon': 'fa fa-exclamation-circle',
                'title': 'Stock bas',
                'message': f"{article.designation} - {article.quantite_stock} unités",
                'url': f'/produits/article/{article.pk}',
            })
        
        # Alertes caisse
        from caisse.models import CaisseCourante
        caisses_fermees = CaisseCourante.objects.filter(est_ouverte=False)
        for caisse in caisses_fermees:
            alertes.append({
                'type': 'info',
                'icon': 'fa fa-info-circle',
                'title': 'Caisse fermée',
                'message': f"La caisse {caisse.nom} est fermée",
                'url': '/caisse',
            })
        
        # Alertes paie
        from paie.models import Paie
        bulletins_non_valides = Paie.objects.filter(valide=False)
        if bulletins_non_valides.exists():
            alertes.append({
                'type': 'warning',
                'icon': 'fa fa-clock-o',
                'title': 'Bulletins non validés',
                'message': f"{bulletins_non_valides.count()} bulletin(s) en attente de validation",
                'url': '/paie',
            })
        
        # Mettre en cache
        cache.set(cache_key, alertes, cls.CACHE_TIMEOUT)
        
        return alertes
    
    @classmethod
    def get_graphiques(cls) -> Dict[str, Any]:
        """
        Récupère les données pour les graphiques.
        """
        cache_key = cls._get_cache_key('graphiques')
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        from factures.models import Facture
        from django.db.models.functions import TruncMonth
        
        # Ventes des 12 derniers mois
        debut_12_mois = timezone.now() - timedelta(days=365)
        
        ventes_par_mois = Facture.objects.filter(
            date_facture__gte=debut_12_mois,
            actif=True
        ).annotate(
            mois=TruncMonth('date_facture')
        ).values('mois').annotate(
            total=Sum('montant_total')
        ).order_by('mois')
        
        # Top 10 clients
        top_clients = Facture.objects.filter(
            actif=True
        ).values('client__nom').annotate(
            total=Sum('montant_total')
        ).order_by('-total')[:10]
        
        # Ventes par catégorie
        from produits.models import Categorie
        ventes_par_categorie = []
        for categorie in Categorie.objects.filter(actif=True):
            total = Facture.objects.filter(
                details_facture__article__categorie=categorie,
                actif=True
            ).aggregate(total=Sum('montant_total'))['total'] or 0
            if total > 0:
                ventes_par_categorie.append({
                    'categorie': categorie.nom,
                    'total': float(total),
                })
        
        graphiques = {
            'ventes_par_mois': [
                {
                    'mois': item['mois'].strftime('%m/%Y'),
                    'total': float(item['total'] or 0)
                }
                for item in ventes_par_mois
            ],
            'top_clients': [
                {
                    'nom': item['client__nom'],
                    'total': float(item['total'])
                }
                for item in top_clients
            ],
            'ventes_par_categorie': ventes_par_categorie,
        }
        
        # Mettre en cache
        cache.set(cache_key, graphiques, cls.CACHE_TIMEOUT)
        
        return graphiques
    
    @classmethod
    def invalider_cache(cls, pattern: Optional[str] = None) -> None:
        """
        Invalide le cache du dashboard.
        """
        if pattern:
            # Invalider les clés correspondant au pattern
            # Note: nécessite une implémentation selon le backend Redis
            pass
        else:
            # Invalider tout le cache dashboard
            cache.delete_pattern(f"{cls.CACHE_KEY_PREFIX}:*")
    
    @classmethod
    def get_mode_offline_data(cls) -> Dict[str, Any]:
        """
        Récupère les données essentielles pour le mode offline.
        """
        cache_key = cls._get_cache_key('offline_data')
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Données essentielles à mettre en cache pour offline
        offline_data = {
            'statistiques': cls.get_statistiques_generales(),
            'alertes': cls.get_alertes(),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Mettre en cache pour 24h
        cache.set(cache_key, offline_data, 86400)
        
        return offline_data