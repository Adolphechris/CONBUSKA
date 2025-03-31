from django import forms
from .models import Commande, DetailsCommande


class CommandeCreateForm(forms.ModelForm):
    class Meta:
        model = Commande
        exclude = ['numero', 'actif', 'cree_par', 'modifie_par']
        widgets = {
            'date_commande': forms.DateInput(attrs={'class': 'form-control'}),
            'fournisseur': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'devise': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'taux': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ArticleCommandeAddForm(forms.ModelForm):
    class Meta:
        model = DetailsCommande
        fields = ['article', 'qte', 'prix']
        widgets = {
            'article': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'qte': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ArticleCommandeUpdateForm(forms.ModelForm):
    article = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'disabled': True}), required=False)

    class Meta:
        model = DetailsCommande
        fields = ['qte', 'prix']
        widgets = {
            'article': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'qte': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    field_order = ['article', 'qte', 'unite']

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article', None)
        super(ArticleCommandeUpdateForm, self).__init__(*args, **kwargs)
        self.fields['article'].initial = self.article
        self.fields['article'].widget.attrs['readonly'] = True
