from django import forms
from .models import Categorie, Unite, Article


class CategorieCreateForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UniteCreateForm(forms.ModelForm):
    class Meta:
        model = Unite
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class ArticleCreateForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['designation', 'description', 'code_barre', 'categorie', 'unite', 'fournisseur', 'prix_achat',
                  'prix_vente', 'prix_vente_gros', 'devise', 'seuil', 'seuil_gros', 'emplacement', 'photo1', 'photo2']
        widgets = {
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'data-parsley-trigger': "keyup", 'rows': 4,
                                                 'cols': 150}),
            'code_barre': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'unite': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'fournisseur': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'prix_achat': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix_vente': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix_vente_gros': forms.NumberInput(attrs={'class': 'form-control'}),
            'devise': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'seuil': forms.NumberInput(attrs={'class': 'form-control'}),
            'seuil_gros': forms.NumberInput(attrs={'class': 'form-control'}),
            'emplacement': forms.TextInput(attrs={'class': 'form-control'}),
            'photo1': forms.FileInput(attrs={'class': 'form-control'}),
            'photo2': forms.FileInput(attrs={'class': 'form-control'}),
        }
