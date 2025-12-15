import django_filters
from django import forms
from .models import Agent

class AgentFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(
        lookup_expr='icontains',
        label="Nom",
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher un agent'
        })
    )

    class Meta:
        model = Agent
        fields = ['matricule', 'nom']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.form.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })