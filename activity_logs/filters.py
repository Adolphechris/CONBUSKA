import django_filters
from django import forms

from .models import ActivityLog


class ActivityLogFilter(django_filters.FilterSet):
    date_debut = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__gte',
        label='Du',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control input-sm'}),
    )
    date_fin = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__lte',
        label='Au',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control input-sm'}),
    )
    user = django_filters.CharFilter(
        field_name='user__username',
        lookup_expr='icontains',
        label='Utilisateur',
        widget=forms.TextInput(attrs={'class': 'form-control input-sm', 'placeholder': 'Nom d\'utilisateur'}),
    )
    module = django_filters.ChoiceFilter(
        choices=[('', 'Tous les modules')] + ActivityLog.MODULE_CHOICES,
        label='Module',
        widget=forms.Select(attrs={'class': 'form-control input-sm'}),
        empty_label=None,
    )
    action = django_filters.ChoiceFilter(
        choices=[('', 'Toutes les actions')] + ActivityLog.ACTION_CHOICES,
        label='Action',
        widget=forms.Select(attrs={'class': 'form-control input-sm'}),
        empty_label=None,
    )

    class Meta:
        model = ActivityLog
        fields = ['date_debut', 'date_fin', 'user', 'module', 'action']
