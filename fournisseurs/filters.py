import django_filters
from django import forms
from .models import Fournisseur

class FournisseurFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(
        lookup_expr='icontains',
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un fournisseur'
        })
    )

    class Meta:
        model = Fournisseur
        fields = ['nom']