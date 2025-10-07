from django import forms
from .models import MouvementCaisse, RubriqueCaisse
from django.urls import reverse

class OuvertureCaisseValidateForm(forms.Form):
    pass

class ClotureCaisseValidateForm(forms.Form):
    pass


class CaisseForm(forms.ModelForm):
    class Meta:
        model = MouvementCaisse
        fields = ['type_mouvement', 'rubrique', 'montant', 'motif']
        widgets = {
            'type_mouvement': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'rubrique': forms.Select(attrs={'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant'}),
            'motif': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Motif'}),
        }


    def __init__(self, *args, **kwargs):
        self.caisse_pk = kwargs.pop('caisse_pk', None)
        super().__init__(*args, **kwargs)
        self.fields['rubrique'].queryset = RubriqueCaisse.objects.filter(visible=True)
        self.fields['rubrique'].widget.attrs.update({
            'hx-get': reverse('rubrique_champ',  kwargs={'caisse_pk': self.caisse_pk}),
            'hx-target': '#rubrique-dependent-fields',
            'hx-trigger': 'change'
        })
