from django import forms
from .models import Parametre, Magasin


class ParametresForm(forms.ModelForm):

    class Meta:
        model = Parametre
        exclude = ['code', 'date_creation', 'date_modification']
        widgets = {
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'societe': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'rccm': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'idnat': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'impot': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'tva': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'pays': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'adresse': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'ville': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'disabled': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'disabled': True}),
            'taux': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Taux', 'disabled': True}),
        }

    def __init__(self, *args, **kwargs):
        super(ParametresForm, self).__init__(*args, **kwargs)
        self.fields['sigle'].initial = self.instance.sigle


class ParametresEditForm(forms.ModelForm):

    class Meta:
        model = Parametre
        exclude = ['code', 'date_creation', 'date_modification']
        widgets = {
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control'}),
            'societe': forms.TextInput(attrs={'class': 'form-control'}),
            'rccm': forms.TextInput(attrs={'class': 'form-control'}),
            'idnat': forms.TextInput(attrs={'class': 'form-control'}),
            'impot': forms.TextInput(attrs={'class': 'form-control'}),
            'tva': forms.TextInput(attrs={'class': 'form-control'}),
            'pays': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'taux': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Taux'}),
        }


class MagasinCreateForm(forms.ModelForm):
    class Meta:
        model = Magasin
        exclude = ['is_principal']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'localisation': forms.TextInput(attrs={'class': 'form-control'}),
        }
