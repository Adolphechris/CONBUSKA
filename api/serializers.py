from rest_framework import serializers
from produits.models import Article, Categorie
from parametres.models import TauxEchange


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'description']


class ArticleSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    prix_fc = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'code', 'nom', 'description', 'categorie', 'categorie_nom',
            'prix_vente', 'prix_fc', 'valeur_usd', 'image_url',
            'est_publie', 'stock_dispo'
        ]

    def get_prix_fc(self, obj):
        try:
            taux = TauxEchange.get_taux_usd_cdf()
            if obj.valeur_usd and taux:
                return round(obj.valeur_usd * taux, 2)
            return obj.prix_vente
        except Exception:
            return obj.prix_vente

    def get_image_url(self, obj):
        if obj.photo1:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo1.url)
        return None


class ArticleListSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    prix_fc = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'code', 'nom', 'categorie_nom', 'prix_vente',
            'prix_fc', 'valeur_usd', 'image_url', 'est_publie'
        ]

    def get_prix_fc(self, obj):
        try:
            taux = TauxEchange.get_taux_usd_cdf()
            if obj.valeur_usd and taux:
                return round(obj.valeur_usd * taux, 2)
            return obj.prix_vente
        except Exception:
            return obj.prix_vente