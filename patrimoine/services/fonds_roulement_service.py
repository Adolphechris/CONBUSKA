from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, F, DecimalField, ExpressionWrapper


class FondsRoulementService:

    RUBRIQUES_EJ_CAISSE = {"Créanciers"}
    RUBRIQUES_SJ = {"Créanciers", "Charges exploitation", "Charges personnelles"}

    @staticmethod
    def _get_taux():
        from parametres.models import get_taux_usd_cdf
        return get_taux_usd_cdf()

    # ------------------------------------------------------------------
    # EJ : Entrées du Jour
    # Résultats bruts approvisionnements du jour + apports créanciers
    # ------------------------------------------------------------------
    @staticmethod
    def compute_ej(date):
        from caisse.models import MouvementCaisse
        from patrimoine.models import ResultatJournalier

        resultat = ResultatJournalier.objects.filter(date=date).first()
        resultat_appros = resultat.resultat_brut if resultat else Decimal("0")

        apports_creanciers = (
            MouvementCaisse.objects
            .filter(
                date_mouvement__date=date,
                type_mouvement="ENTREE",
                rubrique__nom__in=FondsRoulementService.RUBRIQUES_EJ_CAISSE,
            )
            .aggregate(total=Sum("montant"))["total"] or Decimal("0")
        )

        return resultat_appros + apports_creanciers

    # ------------------------------------------------------------------
    # SJ : Sorties du Jour
    # Remboursements créanciers + charges exploitation + charges personnelles
    # ------------------------------------------------------------------
    @staticmethod
    def compute_sj(date):
        from caisse.models import MouvementCaisse

        total = (
            MouvementCaisse.objects
            .filter(
                date_mouvement__date=date,
                type_mouvement="SORTIE",
                rubrique__nom__in=FondsRoulementService.RUBRIQUES_SJ,
            )
            .aggregate(total=Sum("montant"))["total"] or Decimal("0")
        )

        return total

    # ------------------------------------------------------------------
    # Contre-vérification : FR = TVMS + TSC + TSCl - TSCF
    # ------------------------------------------------------------------
    @staticmethod
    def compute_contreverification():
        detail = FondsRoulementService.compute_contreverification_detail()
        return detail["tvms"] + detail["tsc"] + detail["tscl"] - detail["tscf"]

    @staticmethod
    def compute_contreverification_detail():
        tvms = FondsRoulementService._compute_tvms()
        tsc = FondsRoulementService._compute_tsc()
        tscl = FondsRoulementService._compute_tscl()
        tscf = FondsRoulementService._compute_tscf()
        return {
            "tvms": tvms,
            "tsc": tsc,
            "tscl": tscl,
            "tscf": tscf,
            "total": tvms + tsc + tscl - tscf,
        }

    @staticmethod
    def _compute_tvms():
        """Valeur totale des marchandises en stock au coût d'achat."""
        from produits.models import Stock

        taux = FondsRoulementService._get_taux()

        stocks = (
            Stock.objects
            .select_related("article")
            .filter(qte__gt=0)
        )

        total = Decimal("0")
        for s in stocks:
            prix = s.article.prix_achat
            if s.article.devise == "$":
                prix = prix * taux
            total += prix * s.qte

        return total

    @staticmethod
    def _compute_tsc():
        """Somme des soldes de fermeture les plus récents par caisse."""
        from patrimoine.models import SnapshotJournalier
        from caisse.models import Caisse

        total = Decimal("0")
        for caisse in Caisse.objects.all():
            dernier = (
                SnapshotJournalier.objects
                .filter(caisse=caisse)
                .order_by("-date")
                .first()
            )
            if dernier:
                total += dernier.solde_fermeture

        return total

    @staticmethod
    def _compute_tscl():
        """Somme des soldes des comptes clients (créances)."""
        from clients.models import Client

        total = Decimal("0")
        for client in Client.objects.all():
            solde = client.solde()
            if solde and solde > 0:
                total += solde

        return total

    @staticmethod
    def _compute_tscf():
        """Somme des soldes des comptes fournisseurs (dettes)."""
        from fournisseurs.models import Fournisseur

        total = Decimal("0")
        for fournisseur in Fournisseur.objects.all():
            solde = fournisseur.solde()
            if solde and solde > 0:
                total += solde

        return total

    # ------------------------------------------------------------------
    # rebuild : calcule et persiste le snapshot FR pour une date donnée
    # ------------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def rebuild(date):
        from patrimoine.models import FondsRoulementSnapshot

        import datetime

        veille = date - datetime.timedelta(days=1)
        precedent = FondsRoulementSnapshot.objects.filter(date=veille).first()

        if precedent:
            fr_initial = precedent.fr_final
        else:
            # Premier snapshot : l'initial est la contre-vérification du moment
            # (transposition du patrimoine existant avant le début du suivi)
            fr_initial = FondsRoulementService.compute_contreverification()

        ej = FondsRoulementService.compute_ej(date)
        sj = FondsRoulementService.compute_sj(date)
        fr_final = fr_initial + ej - sj
        fr_contreverif = FondsRoulementService.compute_contreverification()
        ecart = fr_final - fr_contreverif

        FondsRoulementSnapshot.objects.update_or_create(
            date=date,
            defaults={
                "fr_initial": fr_initial,
                "ej": ej,
                "sj": sj,
                "fr_final": fr_final,
                "fr_contreverif": fr_contreverif,
                "ecart": ecart,
            }
        )
