from django import forms
from django.core.exceptions import ValidationError
from factures.models import DetailsFacture
from produits.models import Article, Stock
from parametres.models import Magasin

class InfosFactureForm(forms.Form):
    livreur = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                            'placeholder': 'Livreur',
                                                            'disabled': True}), required=False)
    client = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control',
                                                           'placeholder': 'Client'}), required=False)

    def __init__(self, *args, **kwargs):
        self.livreur = kwargs.pop('livreur', None)
        super(InfosFactureForm, self).__init__(*args, **kwargs)
        self.fields['livreur'].initial = self.livreur


class ArticleFactureAddForm(forms.ModelForm):
    article = forms.ModelChoiceField(
        queryset=Article.objects.all(),
        empty_label="--- Sélectionner un article ---",
        widget = forms.Select(attrs={'class': 'form-control js-simple-select'}),
    )
    class Meta:
        model = DetailsFacture
        fields = ['qte']
        widgets = {
            'qte': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        article = cleaned_data.get("article")
        qte = cleaned_data.get("qte")

        get_magasin = Magasin.objects.get(nom="Alimentation")
        stock = sum(i.qte for i in Stock.objects.filter(article=article.pk, magasin=get_magasin.pk))

        if qte > stock:
            raise ValidationError("La quantité est supérieure à la quantité en stock.")



class ArticleFactureUpdateForm(forms.ModelForm):
    class Meta:
        model = DetailsFacture
        fields = ['article', 'qte']
        widgets = {
            'article': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'qte': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        article = cleaned_data.get("article")
        qte = cleaned_data.get("qte")

        get_magasin = Magasin.objects.get(nom="Alimentation")
        stock = sum(i.qte for i in Stock.objects.filter(article=article.pk, magasin=get_magasin.pk))

        if qte > stock:
            raise ValidationError("La quantité est supérieure à la quantité en stock.")
