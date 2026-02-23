from approvisionnements.models import FraisApprovisionnement

class FraisService:

    @staticmethod
    def save_frais(detail, cleaned_data):
        # supprimer anciens frais
        detail.frais.all().delete()

        frais_to_create = []

        for key, value in cleaned_data.items():
            if key.startswith("frais_") and value and value > 0:
                type_id = key.split("_")[1]

                frais_to_create.append(
                    FraisApprovisionnement(
                        detail=detail,
                        type_frais_id=type_id,
                        montant=value
                    )
                )

        if frais_to_create:
            FraisApprovisionnement.objects.bulk_create(frais_to_create)