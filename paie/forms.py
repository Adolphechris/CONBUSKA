from django import forms
from .models import Agent, DetailsPaie


class AgentCreateForm(forms.ModelForm):
    class Meta:
        model = Agent
        exclude = ['matricule']
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'salaire': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PaiePeriodeForm(forms.Form):
    mois = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control'}),
        input_formats=['%Y-%m-%d'],
        required=True,
        label="Mois de la paie"
    )


class PaieCreateForm(forms.ModelForm):
    class Meta:
        model = DetailsPaie
        exclude = ['paie', 'agent', 'salaire']
        widgets = {
            'montant_percu': forms.NumberInput(attrs={'class': 'form-control'}),
            'jap': forms.NumberInput(attrs={'class': 'form-control'}),
            'jp': forms.NumberInput(attrs={'class': 'form-control'}),
            'absence': forms.NumberInput(attrs={'class': 'form-control'}),
        }