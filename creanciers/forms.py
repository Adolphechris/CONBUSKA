from django import forms
from .models import Creancier


class CreancierCreateForm(forms.ModelForm):
    class Meta:
        model = Creancier
        exclude = ['code']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
        }
