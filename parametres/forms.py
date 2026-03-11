from django import forms
from .models import Parametre, Magasin, TauxEchange


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


class TauxEchangeForm(forms.ModelForm):
    class Meta:
        model   = TauxEchange
        exclude = ['date_creation', 'date_modification']
        widgets = {
            'devise_source':  forms.Select(attrs={'class': 'form-control'}),
            'devise_cible':   forms.Select(attrs={'class': 'form-control'}),
            'taux':           forms.NumberInput(attrs={
                'class': 'form-control',
                'step':  '0.0001',
                'min':   '0',
            }),
            'effective_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        source = cleaned.get('devise_source')
        cible  = cleaned.get('devise_cible')
        if source and cible and source == cible:
            raise forms.ValidationError(
                "La devise source et la devise cible ne peuvent pas être identiques."
            )
        return cleaned