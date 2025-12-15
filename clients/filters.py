import django_filters
from django import forms
from .models import Client

class ClientFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(
        lookup_expr='icontains',
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un client'
        })
    )

    class Meta:
        model = Client
        fields = ['nom']