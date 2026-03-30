import datetime
from decimal import Decimal

from django.db.models import Sum, F, ExpressionWrapper, DecimalField

from caisse.models import CaisseCourante


def get_total_ventes_comptoir_par_date(date: datetime.date) -> Decimal:
    """
    Ventes comptoir validées pour une date donnée, indépendamment de la session.

    Règles métier :
    - Uniquement les factures validées (`valide=True`).
    - Les factures liées à un compte `FactureClient` sont exclues : elles
      correspondent à des ventes à crédit dont le règlement est géré dans le
      module client et ne doivent pas alimenter la caisse.

    Calculé en deux requêtes agrégées (sans charger les objets en mémoire) :
      total = Σ(qte × prix) sur les lignes – Σ(remise) sur les factures.

    Utilisée par le snapshot journalier et les rapports qui agrègent sur une
    plage de dates sans avoir accès à une `CaisseCourante` ouverte.
    """
    from factures.models import DetailsFacture, Facture

    filtre_factures = dict(
        facture__date_facture=date,
        facture__valide=True,
        facture__facture_client__isnull=True,
    )

    sum_lignes = (
        DetailsFacture.objects
        .filter(**filtre_factures)
        .aggregate(
            total=Sum(
                ExpressionWrapper(F("qte") * F("prix"), output_field=DecimalField(max_digits=18, decimal_places=2))
            )
        )["total"] or Decimal("0")
    )

    sum_remises = (
        Facture.objects
        .filter(date_facture=date, valide=True, facture_client__isnull=True)
        .aggregate(total=Sum("remise"))["total"] or Decimal("0")
    )

    return sum_lignes - sum_remises


def get_total_ventes_caisse(*, caisse_courante: CaisseCourante | None) -> Decimal:
    """
    Ventes comptoir du jour pour la caisse principale (session ouverte).

    Délègue à `get_total_ventes_comptoir_par_date` en utilisant la date
    d'ouverture de la session comme date de référence.
    """
    if not caisse_courante or not caisse_courante.caisse.is_principal:
        return Decimal("0")

    return get_total_ventes_comptoir_par_date(caisse_courante.date_ouverture.date())
