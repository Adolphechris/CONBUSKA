from django import forms
from fournisseurs.models import Fournisseur
from .models import Approvisionnement, DetailsApprovisionnement, TypeFrais
from produits.models import Article
from utils.custom_field import ArticleChoiceField


class ApprovisionnementCreateForm(forms.ModelForm):
    class Meta:
        model = Approvisionnement
        exclude = ['numero', 'actif', 'cree_par', 'modifie_par']
        widgets = {
            'magasin': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'devise': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'taux': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class DynamicFraisMixin:

    def init_dynamic_frais(self):
        frais_actifs = TypeFrais.objects.filter(actif=True)

        self.dynamic_frais_fields = []

        # Précharger les frais existants si instance existe
        existing_frais = {}
        if self.instance.pk:
            existing_frais = {
                f.type_frais_id: f.montant
                for f in self.instance.frais.all()
            }

        for frais in frais_actifs:
            field_name = f"frais_{frais.id}"

            initial_value = existing_frais.get(frais.id)

            self.fields[field_name] = forms.DecimalField(
                label=frais.nom,
                required=False,
                initial=initial_value,
                decimal_places=2,
                max_digits=12,
                widget=forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "placeholder": frais.nom,
                        "data_icon": frais.icon,
                    }
                )
            )

            self.dynamic_frais_fields.append(field_name)

    @property
    def frais_fields(self):
        for field_name in self.fields:
            if field_name.startswith("frais_"):
                yield self[field_name]


class ArticleApprovisionnementAddForm(DynamicFraisMixin, forms.ModelForm):
    article = ArticleChoiceField(
        queryset=Article.objects.all(),
        empty_label="--- Sélectionner un article ---",
        widget = forms.Select(attrs={'class': 'form-control js-simple-select'}),
    )
    fournisseur = forms.ModelChoiceField(
        queryset=Fournisseur.objects.filter(is_system=False),
        empty_label="--- Sélectionner un fournisseur ---",
        widget=forms.Select(attrs={'class': 'form-control js-simple-select'}),
    )
    class Meta:
        model = DetailsApprovisionnement
        fields = ['qte', 'prix', 'date_peremption', 'facture']
        widgets = {
            'qte': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix'}),
            'date_peremption': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Date de péremption'}),
            'facture': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numero facture'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_dynamic_frais()


class ArticleApprovisionnementUpdateForm(DynamicFraisMixin, forms.ModelForm):
    class Meta:
        model = DetailsApprovisionnement
        fields = ['article', 'fournisseur', 'qte', 'prix', 'date_peremption', 'facture']
        widgets = {
            'article': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'fournisseur': forms.Select(attrs={'class': 'form-control js-simple-select'}),
            'qte': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_peremption': forms.DateInput(attrs={'class': 'form-control'}),
            'facture': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numero facture'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_dynamic_frais()
