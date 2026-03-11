import calendar
from datetime import date

from django import forms
from fournisseurs.models import Fournisseur
from .models import Approvisionnement, DetailsApprovisionnement, TypeFrais
from produits.models import Article
from utils.custom_field import ArticleChoiceField


class DatePeremptionField(forms.Field):
    """
    Champ texte MM/AAAA → retourne le dernier jour du mois comme datetime.date.
    Optionnel par défaut.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('label', 'Date de péremption')
        kwargs.setdefault('widget', forms.TextInput(attrs={
            'class': 'form-control date-peremption-input',
            'placeholder': 'MM/AAAA (ex: 06/2025)',
            'maxlength': '7',
            'autocomplete': 'off',
        }))
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return None
        raw = str(value).strip()
        if not raw:
            return None

        parts = raw.split('/')
        if len(parts) != 2:
            raise forms.ValidationError("Format attendu : MM/AAAA (ex: 06/2025).")

        try:
            month = int(parts[0])
            year = int(parts[1])
        except ValueError:
            raise forms.ValidationError("Format attendu : MM/AAAA (ex: 06/2025).")

        if not (1 <= month <= 12):
            raise forms.ValidationError("Le mois doit être entre 01 et 12.")
        if len(parts[1]) != 4 or year < 2000 or year > 2100:
            raise forms.ValidationError("L'année doit être sur 4 chiffres et comprise entre 2000 et 2100.")

        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, last_day)

    def prepare_value(self, value):
        """Affiche MM/AAAA quand le formulaire est pré-rempli (update)."""
        if isinstance(value, date):
            return value.strftime('%m/%Y')
        return value or ''


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
    date_peremption = DatePeremptionField()

    class Meta:
        model = DetailsApprovisionnement
        fields = ['qte', 'prix', 'date_peremption', 'facture']
        widgets = {
            'qte': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix'}),
            'facture': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numero facture'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_dynamic_frais()


class ArticleApprovisionnementUpdateForm(DynamicFraisMixin, forms.ModelForm):
    """
    Formulaire de modification d'une ligne d'approvisionnement.
    L'article et le fournisseur sont verrouillés sur l'instance existante —
    ils définissent l'identité de la ligne et ne peuvent pas être changés.
    Seuls qte, prix, date_peremption, facture et les frais sont modifiables.
    """
    date_peremption = DatePeremptionField()

    class Meta:
        model = DetailsApprovisionnement
        fields = ['qte', 'prix', 'date_peremption', 'facture']
        widgets = {
            'qte': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
            'facture': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numero facture'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_dynamic_frais()
