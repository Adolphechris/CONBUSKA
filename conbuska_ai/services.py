"""
conbuska_ai/services.py

Services d'intelligence artificielle pour Conbuska.
Intégration Google Gemini + RAG métier.
"""

from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

try:
    import google.generativeai as genai
except ImportError:
    genai = None
    import logging
    logging.getLogger(__name__).warning("google.generativeai non installé — mode IA désactivé")


class ConbuskaAIService:
    """
    Service principal pour l'assistant IA Conbuska.
    
    Fonctionnalités :
    - Chat intelligent avec contexte métier
    - Analyse de données et recommandations
    - Génération de rapports automatiques
    - Aide à la décision
    """
    
    def __init__(self):
        """Initialise le service avec l'API Gemini."""
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if api_key and genai is not None:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
    
    def chat(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Envoie un message à l'assistant IA et retourne la réponse.
        
        Args:
            message: Message de l'utilisateur
            context: Contexte métier (utilisateur, module, etc.)
        
        Returns:
            Dict avec la réponse et des métadonnées
        """
        if not self.model:
            return {
                'response': "Service IA non configuré. Veuillez ajouter GEMINI_API_KEY dans les paramètres.",
                'error': True
            }
        
        # Construire le prompt avec contexte métier
        system_prompt = self._build_system_prompt(context)
        
        try:
            response = self.model.generate_content(
                f"{system_prompt}\n\nUtilisateur: {message}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                )
            )
            
            return {
                'response': response.text,
                'error': False,
                'timestamp': timezone.now().isoformat(),
            }
        except Exception as e:
            return {
                'response': f"Erreur lors de la génération: {str(e)}",
                'error': True,
                'timestamp': timezone.now().isoformat(),
            }
    
    def _build_system_prompt(self, context: Optional[Dict] = None) -> str:
        """
        Construit le prompt système avec le contexte métier Conbuska.
        """
        prompt = """Tu es Conbuska AI, un assistant intelligent spécialisé dans la gestion d'entreprise.

Contexte métier :
- Gestion de stock (articles, catégories, approvisionnements)
- Gestion des ventes (factures, clients)
- Gestion des commandes fournisseurs
- Gestion de la paie (agents, bulletins, CNSS, IPR)
- Gestion de caisse (mouvements, caisses)
- Gestion du patrimoine (capitaux, emprunts, fonds de roulement)
- Gestion des créanciers et fournisseurs
- Rapports et statistiques

Règles :
- Réponds en français
- Sois précis et professionnel
- Utilise des exemples concrets quand c'est pertinent
- Si tu ne sais pas, dis-le clairement
- Pour les calculs, sois rigoureux
"""
        
        if context:
            if context.get('module'):
                prompt += f"\nModule actuel : {context['module']}"
            if context.get('user_role'):
                prompt += f"\nRôle utilisateur : {context['user_role']}"
        
        return prompt
    
    def analyser_ventes(self, periode_jours: int = 30) -> Dict[str, Any]:
        """
        Analyse les ventes et génère des recommandations.
        """
        from factures.models import Facture
        
        date_debut = timezone.now() - timedelta(days=periode_jours)
        
        factures = Facture.objects.filter(
            date_facture__gte=date_debut,
            actif=True
        )
        
        total_ventes = sum(f.total for f in factures)
        nb_factures = factures.count()
        
        # Top clients
        from factures.models import FactureClient
        top_clients = []
        for fc in FactureClient.objects.filter(
            facture__in=factures
        ).select_related('client').prefetch_related('facture__facture_details'):
            total_client = sum(
                (l.qte * l.prix) for l in fc.facture.facture_details.all()
            )
            top_clients.append({
                'client__nom': fc.client.nom,
                'total': float(total_client),
            })
        top_clients.sort(key=lambda x: x['total'], reverse=True)
        top_clients = top_clients[:5]
        
        return {
            'periode': f"{periode_jours} derniers jours",
            'total_ventes': float(total_ventes),
            'nb_factures': nb_factures,
            'moyenne_par_facture': float(total_ventes / nb_factures) if nb_factures > 0 else 0,
            'top_clients': list(top_clients),
        }
    
    def analyser_stock(self) -> Dict[str, Any]:
        """
        Analyse le stock et génère des alertes.
        """
        from produits.models import Article
        
        articles = Article.objects.filter(actif=True)
        
        # Articles en stock bas
        stock_bas = [a for a in articles if a.stock <= 10]
        
        # Articles en rupture
        rupture = [a for a in articles if a.stock == 0]
        
        # Valeur totale du stock
        valeur_stock = sum(a.stock * float(a.prix_achat) for a in articles)
        
        return {
            'total_articles': articles.count(),
            'articles_stock_bas': len(stock_bas),
            'articles_rupture': len(rupture),
            'valeur_stock': float(valeur_stock),
            'alertes': [
                f"{a.designation}: stock critique ({a.stock})"
                for a in stock_bas[:10]
            ]
        }
    
    def analyser_paie(self, mois: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Analyse la paie d'un mois donné.
        """
        from paie.models import Paie
        
        if mois is None:
            mois = timezone.now().replace(day=1)
        
        bulletins = Paie.objects.filter(mois=mois)
        
        total_salaire_brut = sum(b.salaire_brut for b in bulletins)
        total_net = sum(b.net_a_payer for b in bulletins)
        sum(
            l.montant for b in bulletins
            for l in b.lignes.all()
            if 'CNSS' in l.libelle
        )
        
        return {
            'mois': mois.strftime('%m/%Y'),
            'nb_bulletins': bulletins.count(),
            'total_salaire_brut': float(total_salaire_brut),
            'total_net_a_payer': float(total_net),
            'masse_salariale': float(total_net),
        }
    
    def generer_rapport_automatique(self, type_rapport: str) -> str:
        """
        Génère un rapport automatique en langage naturel.
        """
        if type_rapport == 'ventes':
            analyse = self.analyser_ventes()
            return f"""Rapport des ventes des {analyse['periode']} :

- Chiffre d'affaires total : {analyse['total_ventes']:,.0f} FC
- Nombre de factures : {analyse['nb_factures']}
- Panier moyen : {analyse['moyenne_par_facture']:,.0f} FC

Top 5 clients :
""" + "\n".join(
            f"{i}. {c['client__nom']}: {c['total']:,.0f} FC"
            for i, c in enumerate(analyse['top_clients'], 1)
        )
        
        elif type_rapport == 'stock':
            analyse = self.analyser_stock()
            return f"""Rapport de stock :

- Total articles : {analyse['total_articles']}
- Articles stock bas : {analyse['articles_stock_bas']}
- Articles en rupture : {analyse['articles_rupture']}
- Valeur du stock : {analyse['valeur_stock']:,.0f} FC

Alertes :
""" + "\n".join(
            f"- {alerte}" for alerte in analyse['alertes']
        )
        
        elif type_rapport == 'paie':
            analyse = self.analyser_paie()
            return f"""Rapport de paie {analyse['mois']} :

- Nombre de bulletins : {analyse['nb_bulletins']}
- Masse salariale brute : {analyse['total_salaire_brut']:,.0f} FC
- Masse salariale nette : {analyse['total_net_a_payer']:,.0f} FC"""
        
        return "Type de rapport non reconnu."
    
    def recommander_action(self, module: str) -> List[Dict[str, str]]:
        """
        Génère des recommandations d'actions basées sur l'analyse des données.
        """
        recommandations = []
        
        if module == 'stock':
            analyse = self.analyser_stock()
            if analyse['articles_rupture'] > 0:
                recommandations.append({
                    'priorite': 'haute',
                    'action': 'Réapprovisionner les articles en rupture',
                    'details': f"{analyse['articles_rupture']} article(s) en rupture de stock"
                })
            if analyse['articles_stock_bas'] > 0:
                recommandations.append({
                    'priorite': 'moyenne',
                    'action': 'Commander les articles à stock bas',
                    'details': f"{analyse['articles_stock_bas']} article(s) sous le seuil d'alerte"
                })
        
        elif module == 'ventes':
            analyse = self.analyser_ventes()
            if analyse['nb_factures'] == 0:
                recommandations.append({
                    'priorite': 'haute',
                    'action': 'Relancer les ventes',
                    'details': 'Aucune vente ce mois-ci'
                })
        
        elif module == 'paie':
            analyse = self.analyser_paie()
            recommandations.append({
                'priorite': 'info',
                'action': 'Vérifier les bulletins de paie',
                'details': f"{analyse['nb_bulletins']} bulletin(s) pour {analyse['mois']}"
            })
        
        return recommandations


# Instance singleton
ai_service = ConbuskaAIService()