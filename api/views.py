from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from produits.models import Article, Categorie
from factures.models import Facture, DetailsFacture
from clients.models import Client
from parametres.models import TauxEchange
from .serializers import ArticleListSerializer, ArticleSerializer, CategorieSerializer


class CategorieViewSet(viewsets.ReadOnlyModelViewSet):
    """Liste des catégories d'articles"""
    queryset = Categorie.objects.all().order_by('nom')
    serializer_class = CategorieSerializer
    permission_classes = [permissions.AllowAny]


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Articles publiés pour la boutique"""
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Article.objects.filter(est_publie=True).select_related('categorie').order_by('-id')

    def retrieve(self, request, *args, **kwargs):
        """Détail d'un article"""
        instance = self.get_object()
        serializer = ArticleSerializer(instance, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def nouveautes(self, request):
        """Articles récents"""
        articles = self.get_queryset()[:8]
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """Articles par catégorie"""
        categorie_nom = request.query_params.get('categorie', '')
        if categorie_nom and categorie_nom != 'Tous':
            articles = self.get_queryset().filter(categorie__nom__iexact=categorie_nom)
        else:
            articles = self.get_queryset()
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recherche(self, request):
        """Recherche d'articles"""
        q = request.query_params.get('q', '')
        if q:
            articles = self.get_queryset().filter(nom__icontains=q)
        else:
            articles = self.get_queryset()
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)


class CommandeViewSet(viewsets.ViewSet):
    """Créer une commande depuis la boutique"""
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        """Créer une facture + lignes depuis le panier"""
        data = request.data
        articles_data = data.get('articles', [])
        client_data = data.get('client', {})

        if not articles_data:
            return Response({'error': 'Panier vide'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Créer ou récupérer le client
                client, created = Client.objects.get_or_create(
                    telephone=client_data.get('telephone', ''),
                    defaults={
                        'nom': client_data.get('nom', ''),
                        'email': client_data.get('email', ''),
                        'adresse': client_data.get('adresse', ''),
                        'ville': client_data.get('ville', 'Kinshasa'),
                    }
                )

                # Créer la facture
                facture = Facture.objects.create(
                    client=client,
                    client_comptoir=client_data.get('nom', 'Client boutique'),
                    devise='USD',
                    taux=TauxEchange.get_taux_usd_cdf() or 1,
                    valide=False,  # DRAFT d'abord
                )

                # Créer les lignes
                total_usd = 0
                for item in articles_data:
                    code = item.get('code_article')
                    quantite = item.get('quantite', 1)
                    try:
                        article = Article.objects.get(code=code, est_publie=True)
                        DetailsFacture.objects.create(
                            facture=facture,
                            article=article,
                            quantite=quantite,
                            prix_unitaire=article.prix_vente,
                            valeur_usd=article.valeur_usd or article.prix_vente,
                        )
                        total_usd += (article.valeur_usd or article.prix_vente) * quantite
                    except Article.DoesNotExist:
                        return Response(
                            {'error': f'Article {code} introuvable'},
                            status=status.HTTP_404_NOT_FOUND
                        )

                # Mettre à jour le total
                facture.valeur_usd = total_usd
                facture.save()

                return Response({
                    'success': True,
                    'facture_id': facture.id,
                    'facture_code': facture.code,
                    'total_usd': total_usd,
                    'total_fc': round(total_usd * facture.taux, 2),
                    'message': 'Commande créée avec succès'
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )