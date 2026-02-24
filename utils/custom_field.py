from django import forms

class ArticleChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        stock = getattr(obj, "stock_dispo", 0) or 0
        return f"{obj.designation} | Stock: {stock} | {obj.prix_vente}FC | {obj.prix_vente_gros}FC"