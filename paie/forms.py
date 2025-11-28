from django import forms
from .models import Agent, Paie


class AgentCreateForm(forms.ModelForm):
    class Meta:
        model = Agent
        exclude = ['matricule']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control'}),
            'date_engagement': forms.DateInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'salaire': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PaieCreateForm(forms.ModelForm):
    mois = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control'}),
        input_formats=['%Y-%m-%d'],
        required=True,
        label="Mois de la paie"
    )
    class Meta:
        model = Paie
        exclude = ['agent', 'salaire', 'jap', 'jp', 'montant_percu', 'cree_par', 'modifie_par', 'valide']
        widgets = {
            'absence': forms.NumberInput(attrs={'class': 'form-control'}),
        }
