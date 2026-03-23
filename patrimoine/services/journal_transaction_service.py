from django.db.models import Value, F, CharField, DecimalField, Sum
from django.db.models.functions import Cast
from dataclasses import dataclass, field
from typing import Optional
from caisse.models import MouvementCaisse
from patrimoine.models import ResultatApprovisionnementSnapshot
from patrimoine.services.snapshot_service import SnapshotService
from decimal import Decimal
import datetime
from django.utils.timezone import make_aware

@dataclass
class JournalLine:
    date_mouvement: datetime.datetime
    caisse: str
    motif: str
    rubrique_nom: str
    montant: Decimal
    type_mouvement: str  # ENTREE ou SORTIE
    source: str
    badge_entite: Optional[str] = None


class JournalTransactionService:

    @staticmethod
    def get_lines(date_debut, date_fin):

        lines = []

        # ===============================
        # 1️⃣ MOUVEMENTS CAISSE
        # ===============================

        mouvements = (
            MouvementCaisse.objects
            .select_related("caisse", "rubrique", "sous_rubrique", "caisse_destination")
            .prefetch_related(
                "mouvements_caisse_f__fournisseur",
                "mouvements_caisse_c__client",
                "mouvements_caisse_cr__creancier",
                "mouvements_caisse_db__debiteur",
                "mouvements_caisse_ag__agent",
                "mouvements_caisse_ce__sous_rubrique",
                "mouvements_caisse_cp__sous_rubrique",
            )
            .filter(date_mouvement__date__range=(date_debut, date_fin))
            .exclude(rubrique__nom__in=SnapshotService.EXCLUDED_RUBRIQUES)
        )

        for m in mouvements:
            lines.append(
                JournalLine(
                    date_mouvement=m.date_mouvement,
                    caisse=str(m.caisse),
                    motif=m.motif,
                    rubrique_nom=m.rubrique.nom if m.rubrique else "",
                    montant=m.montant,
                    type_mouvement=m.type_mouvement,
                    source="CAISSE",
                    badge_entite=m.badge_entite,
                )
            )

        # ===============================
        # 2️⃣ RESULTATS APPROVISIONNEMENT
        # ===============================

        appros = (
            ResultatApprovisionnementSnapshot.objects
            .filter(date__range=(date_debut, date_fin))
        )

        for a in appros:
            lines.append(
                JournalLine(
                    date_mouvement=make_aware(
                        datetime.datetime.combine(a.date, datetime.time.min)
                    ),
                    caisse=f'Approvisionnement #{str(a.approvisionnement.numero)}',
                    motif="Résultat brut approvisionnement",
                    rubrique_nom="APPROVISIONNEMENT",
                    montant=a.resultat_brut,
                    type_mouvement="ENTREE",
                    source="APPRO"
                )
            )

        # ===============================
        # TRI GLOBAL
        # ===============================

        lines.sort(key=lambda x: x.date_mouvement, reverse=True)

        return lines