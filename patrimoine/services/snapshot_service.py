from decimal import Decimal

from caisse.models import MouvementCaisse, CaisseCourante
from approvisionnements.models import Approvisionnement
from patrimoine.models import SnapshotJournalier, ResultatApprovisionnementSnapshot, ResultatJournalier, ResultatMensuel
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum


class SnapshotService:

    EXCLUDED_RUBRIQUES = {"Clients", "Fournisseurs", "Transfert caisse"}

    @staticmethod
    @transaction.atomic
    def rebuild_day(*, caisse_courante: CaisseCourante, date):
        caisse = caisse_courante.caisse

        if SnapshotJournalier.objects.filter(
            caisse=caisse, date=date, est_cloture=True
        ).exists():
            raise ValidationError("Journée déjà clôturée")

        mouvements = (
            MouvementCaisse.objects
            .select_related("rubrique")
            .filter(
                caisse=caisse_courante,
                date_mouvement__date=date,
            )
            .exclude(
                rubrique__nom__in=SnapshotService.EXCLUDED_RUBRIQUES
            )
        )

        total_entrees = (
            mouvements.filter(type_mouvement="ENTREE")
            .aggregate(total=Sum("montant"))["total"] or Decimal("0")
        )

        # Les ventes comptoir (factures validées hors FactureClient) alimentent
        # la caisse principale mais ne génèrent pas de MouvementCaisse.
        # On les intègre ici pour que solde_fermeture soit cohérent avec
        # CaisseCourante.solde_final et que _compute_tsc() du FR soit juste.
        if caisse.is_principal:
            from caisse.selectors import get_total_ventes_comptoir_par_date
            total_entrees += get_total_ventes_comptoir_par_date(date)

        total_sorties = (
            mouvements.filter(type_mouvement="SORTIE")
            .aggregate(total=Sum("montant"))["total"] or Decimal("0")
        )

        previous = (
            SnapshotJournalier.objects
            .filter(caisse=caisse, date__lt=date)
            .order_by("-date")
            .first()
        )

        solde_ouverture = (
            previous.solde_fermeture
            if previous
            else caisse_courante.solde_initial
        )

        # Calculer le solde de fermeture
        solde_fermeture = solde_ouverture + total_entrees - total_sorties
        
        # Dual currency: calculer la valeur USD
        from parametres.models import get_taux_usd_cdf
        taux = get_taux_usd_cdf(date)
        solde_fermeture_usd = (solde_fermeture / taux) if taux else None

        SnapshotJournalier.objects.update_or_create(
            caisse=caisse,
            date=date,
            defaults={
                "solde_ouverture": solde_ouverture,
                "total_entrees": total_entrees,
                "total_sorties": total_sorties,
                "solde_fermeture": solde_fermeture,
                "solde_fermeture_usd": solde_fermeture_usd,
            }
        )

    @staticmethod
    def capture_approvisionnement(*, approvisionnement:Approvisionnement, date):
        """
        Cette method génère un snapshot de résultat/CA pour chaque appro, un snapshot journalier et mensuel des appros
        :param approvisionnement:
        :param date:
        :return:
        """
        from parametres.models import get_taux_usd_cdf
        from decimal import Decimal
        
        taux = get_taux_usd_cdf(date)
        taux_dec = Decimal(str(taux)) if taux else None
        
        # Calculer les valeurs USD
        resultat_brut_usd = (Decimal(str(approvisionnement.resultat_total)) / taux_dec) if taux_dec else None
        cout_achat_usd = (Decimal(str(approvisionnement.cout_achat)) / taux_dec) if taux_dec else None
        frais_achat_usd = (Decimal(str(approvisionnement.frais_achat_total)) / taux_dec) if taux_dec else None
        chiffre_affaires_usd = (Decimal(str(approvisionnement.chiffre_affaires)) / taux_dec) if taux_dec else None
        
        ResultatApprovisionnementSnapshot.objects.update_or_create(
            approvisionnement=approvisionnement,
            date=date,
            defaults={
                "devise": approvisionnement.devise,
                "taux": approvisionnement.taux,
                "resultat_brut": approvisionnement.resultat_total,
                "cout_achat": approvisionnement.cout_achat,
                "frais_achat": approvisionnement.frais_achat_total,
                "chiffre_affaires": approvisionnement.chiffre_affaires,
                "resultat_brut_usd": resultat_brut_usd,
                "cout_achat_usd": cout_achat_usd,
                "frais_achat_usd": frais_achat_usd,
                "chiffre_affaires_usd": chiffre_affaires_usd,
            }
        )

    @staticmethod
    def rebuild_journalier(date):
        from parametres.models import get_taux_usd_cdf
        from decimal import Decimal
        
        agg = ResultatApprovisionnementSnapshot.objects.filter(
            date=date
        ).aggregate(
            resultat_brut=Sum("resultat_brut"),
            chiffre_affaires=Sum("chiffre_affaires"),
            resultat_brut_usd=Sum("resultat_brut_usd"),
            chiffre_affaires_usd=Sum("chiffre_affaires_usd"),
        )

        ResultatJournalier.objects.update_or_create(
            date=date,
            defaults={
                "resultat_brut": agg["resultat_brut"] or 0,
                "chiffre_affaires": agg["chiffre_affaires"] or 0,
                "resultat_brut_usd": agg["resultat_brut_usd"],
                "chiffre_affaires_usd": agg["chiffre_affaires_usd"],
            }
        )

    @staticmethod
    def rebuild_mensuel(annee: int, mois: int):
        agg = ResultatApprovisionnementSnapshot.objects.filter(
            date__year=annee,
            date__month=mois,
        ).aggregate(
            resultat_brut=Sum("resultat_brut"),
            chiffre_affaires=Sum("chiffre_affaires"),
            resultat_brut_usd=Sum("resultat_brut_usd"),
            chiffre_affaires_usd=Sum("chiffre_affaires_usd"),
        )

        ResultatMensuel.objects.update_or_create(
            annee=annee,
            mois=mois,
            defaults={
                "resultat_brut": agg["resultat_brut"] or 0,
                "chiffre_affaires": agg["chiffre_affaires"] or 0,
                "resultat_brut_usd": agg["resultat_brut_usd"],
                "chiffre_affaires_usd": agg["chiffre_affaires_usd"],
            }
        )

    @staticmethod
    def on_approvisionnement_validated(approvisionnement: Approvisionnement):
        from patrimoine.services.fonds_roulement_service import FondsRoulementService

        snapshot_date = approvisionnement.date_creation.date()

        SnapshotService.capture_approvisionnement(
            approvisionnement=approvisionnement,
            date=snapshot_date
        )

        SnapshotService.rebuild_journalier(snapshot_date)
        SnapshotService.rebuild_mensuel(
            snapshot_date.year,
            snapshot_date.month
        )

        FondsRoulementService.rebuild(snapshot_date)

    # ── Helpers lecture ─────────────────────────────────────────────────────

    @staticmethod
    def get_appro_par_jour(date_debut, date_fin) -> dict:
        """
        Retourne {date → Decimal} des résultats bruts d'approvisionnement
        agrégés par jour sur la plage donnée.
        Source de vérité : ResultatApprovisionnementSnapshot.
        """
        rows = (
            ResultatApprovisionnementSnapshot.objects
            .filter(date__range=(date_debut, date_fin))
            .values('date')
            .annotate(total=Sum('resultat_brut'))
        )
        return {r['date']: r['total'] for r in rows}

    @staticmethod
    def get_appro_total(date_debut, date_fin) -> Decimal:
        """
        Total des résultats bruts d'approvisionnement sur la plage donnée.
        """
        result = (
            ResultatApprovisionnementSnapshot.objects
            .filter(date__range=(date_debut, date_fin))
            .aggregate(total=Sum('resultat_brut'))['total']
        )
        return result or Decimal('0')

    @staticmethod
    def on_approvisionnement_rollback(approvisionnement: Approvisionnement):
        from patrimoine.services.fonds_roulement_service import FondsRoulementService

        snapshot_date = approvisionnement.date_creation.date()

        ResultatApprovisionnementSnapshot.objects.filter(
            approvisionnement=approvisionnement
        ).delete()

        SnapshotService.rebuild_journalier(snapshot_date)
        SnapshotService.rebuild_mensuel(
            snapshot_date.year,
            snapshot_date.month
        )

        FondsRoulementService.rebuild(snapshot_date)