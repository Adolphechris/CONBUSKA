from django import forms
from .models import Fournisseur


class FournisseurCreateForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        exclude = ['code']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'tuteur': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'rccm': forms.TextInput(attrs={'class': 'form-control'}),
            'id_nat': forms.TextInput(attrs={'class': 'form-control'}),
            'impot': forms.TextInput(attrs={'class': 'form-control'}),
            'tva': forms.TextInput(attrs={'class': 'form-control'}),
        }
