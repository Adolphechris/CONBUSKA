from django import forms
from django.core.exceptions import ValidationError
from factures.models import Facture, DetailsFacture, FactureClient
from produits.models import Article, Stock
from parametres.models import Magasin
from clients.models import Client
from utils.custom_field import ArticleChoiceField, ArticleSelectWidget

"""
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
"""


class InfosFactureForm(forms.ModelForm):
    class Meta:
        model = Facture
        fields = ['client_comptoir']
        widgets = {
            'client_comptoir': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Client'
            }),
        }

    def save(self, commit=True):
        facture = super().save(commit=False)
        facture.livreur = self.instance.livreur  # on garde le livreur existant
        if commit:
            facture.save()
        return facture


class ArticleFactureAddForm(forms.ModelForm):
    article = ArticleChoiceField(
        queryset=Article.objects.none(),
        empty_label="--- Sélectionner un article ---",
        widget=ArticleSelectWidget(attrs={'class': 'form-control js-simple-select', 'id': 'id_article_add'}),
    )
    class Meta:
        model = DetailsFacture
        fields = ['qte']
        widgets = {
            'qte': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On rafraîchit le queryset à chaque instanciation
        self.fields['article'].queryset = Article.objects.with_stock().available().order_by('designation')

    def clean(self):
        cleaned_data = super().clean()
        article = cleaned_data.get("article")
        qte = cleaned_data.get("qte")

        get_magasin = Magasin.objects.get(is_principal=True)
        stock = sum(i.qte for i in Stock.objects.filter(article=article.pk, magasin=get_magasin.pk))

        if qte > stock:
            raise ValidationError("La quantité est supérieure à la quantité en stock.")



class ArticleFactureUpdateForm(forms.ModelForm):
    """
    Formulaire de modification d'une ligne de facture.
    L'article est verrouillé sur l'instance existante — seule la quantité
    est modifiable. Cela évite tout risque de doublon ou de delta stock erroné.
    """
    class Meta:
        model = DetailsFacture
        fields = ['qte']
        widgets = {
            'qte': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        qte = cleaned_data.get("qte")
        # L'article est toujours celui de l'instance en base — non modifiable.
        article = self.instance.article

        get_magasin = Magasin.objects.get(is_principal=True)
        stock = sum(i.qte for i in Stock.objects.filter(article=article.pk, magasin=get_magasin.pk))

        if qte > stock:
            raise ValidationError("La quantité est supérieure à la quantité en stock.")


class FactureClientForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        empty_label="--- Sélectionner un client ---",
        widget = forms.Select(attrs={'class': 'form-control js-simple-select'}),
    )

    class Meta:
        model = FactureClient
        exclude = ['facture']