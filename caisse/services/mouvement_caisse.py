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
    Caisse,
    CaisseCourante,
    SousRubriqueCaisse,
)

from fournisseurs.models import Fournisseur
from clients.models import Client
from creanciers.models import Creancier, Debiteur
from paie.models import Agent
from patrimoine.services import SnapshotService
from patrimoine.services.fonds_roulement_service import FondsRoulementService


class MouvementCaisseService:
    """
    Couche métier unique pour la gestion des mouvements de caisse.
    Aucune dépendance HTTP / Django Views.

    Contrat : toute création, modification ou suppression de MouvementCaisse
    doit passer par les méthodes publiques (create, update, delete) de ce service.
    La garde unique contre les écritures sur une caisse clôturée est
    _assert_caisse_ouverte(), appelée dans create, update et delete.
    Ne pas surcharger MouvementCaisse.save() pour ce contrôle.
    """
    # ----------------- Guards -----------------

    @staticmethod
    def _assert_caisse_ouverte(caisse_courante: CaisseCourante):
        if not caisse_courante.est_ouverte:
            raise ValidationError("La caisse est clôturée")

    @staticmethod
    def _is_transfert(mouvement: MouvementCaisse) -> bool:
        return (mouvement.rubrique.nom or "").strip().lower() == "transfert caisse"

    @staticmethod
    def _get_transfert_miroir(mouvement: MouvementCaisse) -> Optional[MouvementCaisse]:
        return (
            MouvementCaisse.objects
            .filter(mouvement_transfert_source=mouvement)
            .select_related("caisse")
            .first()
        )

    @classmethod
    def _assign_caisse_destination(cls, mouvement: MouvementCaisse, caisse_destination_id: Optional[int]):
        if cls._is_transfert(mouvement) and caisse_destination_id:
            mouvement.caisse_destination_id = int(caisse_destination_id)
        else:
            mouvement.caisse_destination = None

    @classmethod
    def _assert_not_mirror(cls, mouvement: MouvementCaisse):
        if mouvement.mouvement_transfert_source_id:
            raise ValidationError(
                "Le mouvement miroir d'un transfert ne peut pas être modifié directement."
            )

    @classmethod
    def _cleanup_transfert(cls, mouvement: MouvementCaisse):
        miroir = cls._get_transfert_miroir(mouvement)
        if miroir:
            cls._assert_caisse_ouverte(miroir.caisse)
            miroir.delete()

    @staticmethod
    def _rebuild_impacts(*, impacts):
        unique_impacts = {
            (caisse_courante.pk, date): caisse_courante
            for caisse_courante, date in impacts
            if caisse_courante is not None and date is not None
        }

        for (caisse_pk, date), caisse_courante in unique_impacts.items():
            SnapshotService.rebuild_day(caisse_courante=caisse_courante, date=date)

        for _, date in unique_impacts.keys():
            FondsRoulementService.rebuild(date)

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
            caisse_destination_id: Optional[int] = None,
    ) -> MouvementCaisse:
        cls._assert_caisse_ouverte(caisse_courante)

        if not form.is_valid():
            raise ValueError("Form invalide")

        mouvement = form.save(commit=False)
        mouvement.caisse = caisse_courante
        mouvement.effectue_par = user
        cls._assign_caisse_destination(mouvement, caisse_destination_id)

        mouvement.save()

        # Dispatch vers les tables de liaison (Fournisseur, Client, Créancier, etc.)
        # pour que les rapports patrimoine et soldes tiers restent cohérents.
        extra_impacts = cls._dispatch_with_ids(
            mouvement,
            fournisseur_id=fournisseur_id,
            client_id=client_id,
            creancier_id=creancier_id,
            debiteur_id=debiteur_id,
            agent_id=agent_id,
            sous_rubrique_id=sous_rubrique_id,
            user=user,
            caisse_destination_id=caisse_destination_id,
        )
        cls._rebuild_impacts(
            impacts=[
                (caisse_courante, mouvement.date_mouvement.date()),
                *extra_impacts,
            ]
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
            caisse_destination_id: Optional[int] = None,
    ) -> MouvementCaisse:
        if not form.is_valid():
            raise ValueError("Form invalide")

        mouvement = form.instance
        cls._assert_not_mirror(mouvement)
        cls._assert_caisse_ouverte(mouvement.caisse)

        miroir_avant = cls._get_transfert_miroir(mouvement)
        old_date = mouvement.date_mouvement.date()
        impacts = [(mouvement.caisse, old_date)]
        if miroir_avant:
            cls._assert_caisse_ouverte(miroir_avant.caisse)
            impacts.append((miroir_avant.caisse, miroir_avant.date_mouvement.date()))

        mouvement = form.save(commit=False)
        cls._assign_caisse_destination(mouvement, caisse_destination_id)
        mouvement.save()
        # Mise à jour des liaisons tiers (Fournisseur, Client, Créancier, etc.)
        extra_impacts = cls._dispatch_with_ids(
            mouvement,
            fournisseur_id=fournisseur_id,
            client_id=client_id,
            creancier_id=creancier_id,
            debiteur_id=debiteur_id,
            agent_id=agent_id,
            sous_rubrique_id=sous_rubrique_id,
            user=user,
            caisse_destination_id=caisse_destination_id,
        )

        new_date = mouvement.date_mouvement.date()
        impacts.extend(
            [
                (mouvement.caisse, new_date),
                *extra_impacts,
            ]
        )
        cls._rebuild_impacts(impacts=impacts)

        return mouvement

    @classmethod
    @transaction.atomic
    def delete(cls, *, mouvement: MouvementCaisse):
        cls._assert_not_mirror(mouvement)
        cls._assert_caisse_ouverte(mouvement.caisse)

        date = mouvement.date_mouvement.date()
        impacts = [(mouvement.caisse, date)]
        miroir = cls._get_transfert_miroir(mouvement)
        if miroir:
            cls._assert_caisse_ouverte(miroir.caisse)
            impacts.append((miroir.caisse, miroir.date_mouvement.date()))

        mouvement.delete()
        cls._rebuild_impacts(impacts=impacts)

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
            caisse_destination_id=None,
    ):
        key = (mouvement.rubrique.nom or "").strip().lower()

        if key == "fournisseurs":
            cls._handle_fournisseur(mouvement, fournisseur_id)
        elif key == "clients":
            cls._handle_client(mouvement, client_id)
        elif key == "créanciers":
            cls._handle_creancier(mouvement, creancier_id)
        elif key == "débiteurs":
            cls._handle_debiteur(mouvement, debiteur_id)
        elif key in {"transport", "avance sur salaire", "restauration", "assistance sociale"}:
            cls._handle_agent(mouvement, agent_id)
        elif key in {"charges exploitation", "charges personnelles"}:
            cls._handle_charge(mouvement, sous_rubrique_id)
        elif key == "transfert caisse":
            return cls._handle_transfert(mouvement, user)
        else:
            cls._cleanup_transfert(mouvement)

        return []

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
        if mouvement.type_mouvement != "SORTIE":
            raise ValidationError("Un transfert de caisse doit être enregistré comme une sortie.")

        caisse_destination = getattr(mouvement, "caisse_destination", None)
        miroir = MouvementCaisseService._get_transfert_miroir(mouvement)
        if not caisse_destination:
            if miroir:
                MouvementCaisseService._assert_caisse_ouverte(miroir.caisse)
                miroir.delete()
            return []

        caisse_ouverte = CaisseCourante.objects.filter(
            caisse=caisse_destination,
            est_ouverte=True
        ).select_for_update().first()

        if not caisse_ouverte:
            raise ValidationError(
                f"Impossible de transférer vers « {caisse_destination} » : "
                "veuillez ouvrir cette caisse avant de procéder au transfert."
            )

        if miroir:
            MouvementCaisseService._assert_caisse_ouverte(miroir.caisse)
            miroir.caisse = caisse_ouverte
            miroir.type_mouvement = "ENTREE"
            miroir.rubrique = mouvement.rubrique
            miroir.montant = mouvement.montant
            miroir.motif = mouvement.motif
            miroir.effectue_par = user
            miroir.date_mouvement = mouvement.date_mouvement
            miroir.caisse_destination = None
            miroir.save()
        else:
            miroir = MouvementCaisse.objects.create(
                caisse=caisse_ouverte,
                type_mouvement="ENTREE",
                rubrique=mouvement.rubrique,
                montant=mouvement.montant,
                motif=mouvement.motif,
                effectue_par=user,
                date_mouvement=mouvement.date_mouvement,
                mouvement_transfert_source=mouvement,
            )

        return [(miroir.caisse, miroir.date_mouvement.date())]