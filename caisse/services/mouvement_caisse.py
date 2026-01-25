from django.db import transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from typing import Optional

from caisse.models import (
    MouvementCaisse,
    MouvementCaisseFournisseur,
    MouvementCaisseClient,
    MouvementCaisseCreancier,
    MouvementCaisseDebiteur,
    MouvementCaisseAgent,
    MouvementCaisseChargesExploitation,
    MouvementCaisseChargesPersonnelles,
    CaisseCourante,
    SousRubriqueCaisse,
)

from fournisseurs.models import Fournisseur
from clients.models import Client
from creanciers.models import Creancier, Debiteur
from paie.models import Agent
from patrimoine.services import SnapshotService


class MouvementCaisseService:
    """
    Couche métier unique pour la gestion des mouvements de caisse.
    Aucune dépendance HTTP / Django Views.
    """
    # ----------------- Guards -----------------

    @staticmethod
    def _assert_caisse_ouverte(caisse_courante: CaisseCourante):
        if not caisse_courante.est_ouverte:
            raise ValidationError("La caisse est clôturée")

    # ---------- API PUBLIQUE ----------

    @classmethod
    @transaction.atomic
    def create(
            cls,
            *,
            form,
            caisse_courante: CaisseCourante,
            user,
            fournisseur_id: Optional[int] = None,
            client_id: Optional[int] = None,
            creancier_id: Optional[int] = None,
            debiteur_id: Optional[int] = None,
            agent_id: Optional[int] = None,
            sous_rubrique_id: Optional[int] = None,
    ) -> MouvementCaisse:
        cls._assert_caisse_ouverte(caisse_courante)

        if not form.is_valid():
            raise ValueError("Form invalide")

        mouvement = form.save(commit=False)
        mouvement.caisse = caisse_courante
        mouvement.effectue_par = user
        mouvement.save()

        cls._dispatch_with_ids(
            mouvement,
            fournisseur_id=fournisseur_id,
            client_id=client_id,
            creancier_id=creancier_id,
            debiteur_id=debiteur_id,
            agent_id=agent_id,
            sous_rubrique_id=sous_rubrique_id,
            user=user,
        )

        SnapshotService.rebuild_day(
            caisse_courante=caisse_courante,
            date=mouvement.date_mouvement.date(),
        )

        return mouvement

    @classmethod
    @transaction.atomic
    def update(
            cls,
            *,
            form,
            user,
            fournisseur_id: Optional[int] = None,
            client_id: Optional[int] = None,
            creancier_id: Optional[int] = None,
            debiteur_id: Optional[int] = None,
            agent_id: Optional[int] = None,
            sous_rubrique_id: Optional[int] = None,
    ) -> MouvementCaisse:
        if not form.is_valid():
            raise ValueError("Form invalide")

        mouvement = form.instance
        cls._assert_caisse_ouverte(mouvement.caisse)

        old_date = mouvement.date_mouvement.date()

        mouvement = form.save()
        cls._dispatch_with_ids(mouvement,
                               fournisseur_id=fournisseur_id,
                               client_id=client_id,
                               creancier_id=creancier_id,
                               debiteur_id=debiteur_id,
                               agent_id=agent_id,
                               sous_rubrique_id=sous_rubrique_id,
                               user=user)

        # rebuild ancienne et nouvelle date (si changement)
        SnapshotService.rebuild_day(
            caisse_courante=mouvement.caisse,
            date=old_date,
        )

        SnapshotService.rebuild_day(
            caisse_courante=mouvement.caisse,
            date=mouvement.date_mouvement.date(),
        )

        return mouvement

    @classmethod
    @transaction.atomic
    def delete(cls, *, mouvement: MouvementCaisse):
        cls._assert_caisse_ouverte(mouvement.caisse)

        date = mouvement.date_mouvement.date()
        caisse = mouvement.caisse

        mouvement.delete()

        SnapshotService.rebuild_day(
            caisse_courante=caisse,
            date=date,
        )

    # ---------- CALCULS FINANCIERS ----------

    @staticmethod
    def total_par_type(caisse_courante, type_mouvement):
        return (
                MouvementCaisse.objects
                .filter(caisse=caisse_courante, type_mouvement=type_mouvement)
                .aggregate(total=Sum("montant"))["total"]
                or 0
        )

    # ---------- DISPATCH METIER ----------

    # ------------------------------------------------------------------
    # Internal dispatch
    # ------------------------------------------------------------------

    @classmethod
    def _dispatch_with_ids(
            cls,
            mouvement: MouvementCaisse,
            *,
            fournisseur_id,
            client_id,
            creancier_id,
            debiteur_id,
            agent_id,
            sous_rubrique_id,
            user,
    ):
        key = (mouvement.rubrique.nom or "").strip().lower()

        if key == "fournisseurs":
            cls._handle_fournisseur(mouvement, fournisseur_id)
        elif key == "clients":
            cls._handle_client(mouvement, client_id)
        elif key == "creanciers":
            cls._handle_creancier(mouvement, creancier_id)
        elif key == "debiteurs":
            cls._handle_debiteur(mouvement, debiteur_id)
        elif key in {"transport", "avance sur salaire", "restauration", "assistance sociale"}:
            cls._handle_agent(mouvement, agent_id)
        elif key in {"charges exploitation", "charges personnelles"}:
            cls._handle_charge(mouvement, sous_rubrique_id)
        elif key == "transfert caisse":
            cls._handle_transfert(mouvement, user)

    # ---------- HANDLERS METIER ----------
    @staticmethod
    def _handle_fournisseur(mouvement, fournisseur_id: Optional[int]):
        if not fournisseur_id:
            return

        if not Fournisseur.objects.filter(pk=fournisseur_id).exists():
            return

        MouvementCaisseFournisseur.objects.update_or_create(
            mouvement_caisse=mouvement,
            defaults={"fournisseur_id": fournisseur_id},
        )

    @staticmethod
    def _handle_client(mouvement, client_id: Optional[int]):
        if not client_id:
            return

        if not Client.objects.filter(pk=client_id).exists():
            return

        MouvementCaisseClient.objects.update_or_create(
            mouvement_caisse=mouvement,
            defaults={"client_id": client_id},
        )

    @staticmethod
    def _handle_creancier(mouvement, creancier_id: Optional[int]):
        if not creancier_id:
            return

        if not Creancier.objects.filter(pk=creancier_id).exists():
            return

        MouvementCaisseCreancier.objects.update_or_create(
            mouvement_caisse=mouvement,
            defaults={"creancier_id": creancier_id},
        )

    @staticmethod
    def _handle_debiteur(mouvement, debiteur_id: Optional[int]):
        if not debiteur_id:
            return

        if not Debiteur.objects.filter(pk=debiteur_id).exists():
            return

        MouvementCaisseDebiteur.objects.update_or_create(
            mouvement_caisse=mouvement,
            defaults={"debiteur_id": debiteur_id},
        )

    @staticmethod
    def _handle_agent(mouvement, agent_id: Optional[int]):
        if not agent_id:
            return

        if not Agent.objects.filter(pk=agent_id).exists():
            return

        MouvementCaisseAgent.objects.update_or_create(
            mouvement_caisse=mouvement,
            defaults={"agent_id": agent_id},
        )

    @staticmethod
    def _handle_charge(mouvement, sous_rubrique_id: Optional[int]):
        if not sous_rubrique_id:
            return

        if not SousRubriqueCaisse.objects.filter(pk=sous_rubrique_id).exists():
            return

        sous_rubrique = SousRubriqueCaisse.objects.get(pk=sous_rubrique_id)
        if sous_rubrique.rubrique.nom == "Charges exploitation":
            MouvementCaisseChargesExploitation.objects.update_or_create(
                mouvement_caisse=mouvement,
                defaults={"sous_rubrique": sous_rubrique},
            )
        else:
            MouvementCaisseChargesPersonnelles.objects.update_or_create(
                mouvement_caisse=mouvement,
                defaults={"sous_rubrique": sous_rubrique},
            )

    @staticmethod
    def _handle_transfert(mouvement, user):
        caisse_destination = getattr(mouvement, "caisse_destination", None)
        if not caisse_destination:
            return

        caisse_ouverte = CaisseCourante.objects.filter(
            caisse=caisse_destination,
            est_ouverte=True
        ).select_for_update().first()

        if not caisse_ouverte:
            return

        MouvementCaisse.objects.create(
            caisse=caisse_ouverte,
            type_mouvement="ENTREE",
            rubrique=mouvement.rubrique,
            montant=mouvement.montant,
            motif=mouvement.motif,
            effectue_par=user,
        )