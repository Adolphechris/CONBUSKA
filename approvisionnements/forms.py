from django import forms
from django.db import transaction
from fournisseurs.models import Fournisseur
from .models import Approvisionnement, DetailsApprovisionnement
from produits.models import Article


class ApprovisionnementCreateForm(forms.ModelForm):
    class Meta:
        model = Approvisionnement
        exclude = ['numero', 'actif', 'cree_par', 'modifie_par']
        widgets = {
            'magasin': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'devise': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'taux': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ArticleApprovisionnementAddForm(forms.ModelForm):
    article = forms.ModelChoiceField(
        queryset=Article.objects.all(),
        empty_label="--- Sélectionner un article ---",
        widget = forms.Select(attrs={'class': 'form-control js-simple-select'}),
    )
    fournisseur = forms.ModelChoiceField(
        queryset=Fournisseur.objects.all(),
        empty_label="--- Sélectionner un fournisseur ---",
        widget=forms.Select(attrs={'class': 'form-control js-simple-select'}),
    )
    class Meta:
        model = DetailsApprovisionnement
        fields = ['qte', 'prix', 'date_peremption', 'facture', 'declaration', 'transport', 'tva', 'manutention',
                  'autre_frais']
        widgets = {
            'qte': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix'}),
            'date_peremption': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Date de péremption'}),
            'facture': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numero facture'}),
            'declaration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Déclaration'}),
            'transport': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Transport'}),
            'tva': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'TVA'}),
            'manutention': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Manutention'}),
            'autre_frais': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Autres frais'}),
        }


class ArticleApprovisionnementUpdateForm(forms.ModelForm):
    class Meta:
        model = DetailsApprovisionnement
        fields = ['article', 'fournisseur', 'qte', 'prix', 'date_peremption', 'facture', 'declaration', 'transport',
                  'tva', 'manutention', 'autre_frais']
        widgets = {
            'article': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'fournisseur': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'qte': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_peremption': forms.DateInput(attrs={'class': 'form-control'}),
            'facture': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numero facture'}),
            'declaration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Déclaration'}),
            'transport': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Transport'}),
            'tva': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'TVA'}),
            'manutention': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Manutention'}),
            'autre_frais': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Autres frais'}),
        }

    # field_order = ['article', 'qte', 'unite', 'date_peremption']

    """
    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article', None)
        self.fournisseur = kwargs.pop('fournisseur', None)
        super(ArticleApprovisionnementUpdateForm, self).__init__(*args, **kwargs)
        self.fields['article'].initial = self.article
        self.fields['fournisseur'].initial = self.fournisseur
        # self.fields['article'].widget.attrs['readonly'] = True
    """