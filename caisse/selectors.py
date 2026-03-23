from decimal import Decimal

from caisse.models import CaisseCourante
from factures.models import Facture


def get_total_ventes_caisse(*, caisse_courante: CaisseCourante | None) -> Decimal:
    """
    Retourne uniquement les ventes comptoir du jour pour la caisse principale.

    Les factures liées à `FactureClient` sont exclues du calcul car elles ne
    doivent pas alimenter les ventes caisse.
    """
    if not caisse_courante or not caisse_courante.caisse.is_principal:
        return Decimal("0")

    factures = Facture.objects.filter(
        date_facture=caisse_courante.date_ouverture.date(),
        valide=True,
        facture_client__isnull=True,
    )
    return sum((facture.total for facture in factures), Decimal("0"))
