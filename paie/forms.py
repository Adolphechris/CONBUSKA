"""
paie/forms.py

Formulaires du module paie.
Validation des données uniquement — aucune logique métier.
"""

import datetime

from django import forms

from paie.models import TypeContrat


class AgentForm(forms.Form):
    """Formulaire création/modification d'un agent. Matricule auto-généré par le service."""

    nom = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    date_naissance = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control'}),
    )
    date_engagement = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    telephone = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    adresse = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    ville = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    salaire = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    poste = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    departement = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    type_contrat = forms.ChoiceField(
        choices=TypeContrat.choices,
        initial=TypeContrat.CDI,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
    )


class PaieCreateForm(forms.Form):
    """Formulaire de saisie d'une paie mensuelle pour un agent."""

    # CharField + type="month" → renvoie "YYYY-MM", parsé dans clean_mois
    mois = forms.CharField(
        widget=forms.DateInput(attrs={
            'type': 'month',
            'class': 'form-control',
        }),
        required=True,
        label="Mois de la paie",
    )
    absence = forms.IntegerField(
        min_value=0,
        max_value=26,
        initial=0,
        required=False,
        label="Jours d'absence",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
    )

    def clean_mois(self):
        mois_raw = self.cleaned_data.get('mois', '').strip()
        try:
            if len(mois_raw) == 7:          # format YYYY-MM (type="month")
                mois = datetime.date.fromisoformat(f"{mois_raw}-01")
            else:                            # format YYYY-MM-DD (fallback)
                mois = datetime.date.fromisoformat(mois_raw)
        except ValueError:
            raise forms.ValidationError("Format invalide. Sélectionnez un mois.")
        if mois > datetime.date.today().replace(day=1):
            raise forms.ValidationError("Impossible de générer la paie dans le futur.")
        return mois
