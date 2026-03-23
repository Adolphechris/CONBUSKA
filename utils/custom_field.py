from django import forms


class ArticleSelectWidget(forms.Select):
    """
    Select widget qui expose les données de prix/seuil en data-attributes
    sur chaque <option>, pour permettre un indicateur de prix côté client.
    """

    def optgroups(self, name, value, attrs=None):
        # Pré-construction du dict pk → données de prix (une seule passe sur le queryset).
        # self.choices est un ModelChoiceIterator dont .queryset est le queryset du field.
        if not hasattr(self, '_articles_data') and hasattr(self.choices, 'queryset'):
            self._articles_data = {
                str(obj.pk): {
                    'data-prix-vente':     str(obj.prix_vente),
                    'data-prix-vente-gros': str(obj.prix_vente_gros),
                    'data-seuil-gros':     str(obj.seuil_gros or 0),
                }
                for obj in self.choices.queryset
            }
        return super().optgroups(name, value, attrs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            pk = str(value.value if hasattr(value, 'value') else value)
            extra = getattr(self, '_articles_data', {}).get(pk)
            if extra:
                option['attrs'].update(extra)
        return option


class ArticleChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        stock = getattr(obj, "stock_dispo", 0) or 0
        return f"{obj.designation} | Stock: {stock} | {obj.prix_vente}FC | {obj.prix_vente_gros}FC"
