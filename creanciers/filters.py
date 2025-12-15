import django_filters
from django import forms
from .models import Creancier, Debiteur

class CreancierFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(
        lookup_expr='icontains',
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un créancier'
        })
    )

    class Meta:
        model = Creancier
        fields = ['nom']


class DebiteurFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(
        lookup_expr='icontains',
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un débiteur'
        })
    )

    class Meta:
        model = Debiteur
        fields = ['nom']