from rest_framework import serializers
from produits.models import Article, Categorie
from parametres.models import TauxEchange


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'description']


class ArticleSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    nom = serializers.CharField(source='designation', read_only=True)
    prix_fc = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    stock_dispo = serializers.IntegerField(read_only=True, default=0)
    valeur_usd = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'code', 'nom', 'designation', 'description',
            'categorie', 'categorie_nom',
            'prix_vente', 'prix_fc', 'valeur_usd', 'image_url',
            'est_publie', 'stock_dispo', 'devise', 'slug',
        ]

    def get_prix_fc(self, obj):
        try:
            taux = TauxEchange.get_taux_usd_cdf()
            if obj.devise == '$' and taux:
                return round(float(obj.prix_vente) * float(taux), 2)
            return float(obj.prix_vente)
        except Exception:
            return float(obj.prix_vente)

    def get_valeur_usd(self, obj):
        try:
            if obj.devise == '$':
                return float(obj.prix_vente)
            taux = TauxEchange.get_taux_usd_cdf()
            if taux:
                return round(float(obj.prix_vente) / float(taux), 2)
            return float(obj.prix_vente)
        except Exception:
            return float(obj.prix_vente)

    def get_image_url(self, obj):
        if obj.photo1:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo1.url)
        return None


class ArticleListSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    nom = serializers.CharField(source='designation', read_only=True)
    prix_fc = serializers.SerializerMethodField()
    valeur_usd = serializers.SerializerMethodField()
    stock_dispo = serializers.IntegerField(read_only=True, default=0)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'code', 'nom', 'categorie_nom',
            'prix_vente', 'prix_fc', 'valeur_usd',
            'image_url', 'est_publie', 'stock_dispo',
        ]

    def get_prix_fc(self, obj):
        try:
            taux = TauxEchange.get_taux_usd_cdf()
            if obj.devise == '$' and taux:
                return round(float(obj.prix_vente) * float(taux), 2)
            return float(obj.prix_vente)
        except Exception:
            return float(obj.prix_vente)

    def get_valeur_usd(self, obj):
        try:
            if obj.devise == '$':
                return float(obj.prix_vente)
            taux = TauxEchange.get_taux_usd_cdf()
            if taux:
                return round(float(obj.prix_vente) / float(taux), 2)
            return float(obj.prix_vente)
        except Exception:
            return float(obj.prix_vente)

    def get_image_url(self, obj):
        if obj.photo1:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo1.url)
        return None
