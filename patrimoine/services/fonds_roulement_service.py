from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum, F, DecimalField, ExpressionWrapper


class FondsRoulementService:

    RUBRIQUES_EJ_CAISSE = {"Créanciers"}
    RUBRIQUES_SJ = {"Créanciers"}

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
        from caisse.models import MouvementCaisse, RubriqueCaisse

        total = (
            MouvementCaisse.objects
            .filter(
                date_mouvement__date=date,
                type_mouvement="SORTIE",
            )
            .filter(
                Q(rubrique__nom__in=FondsRoulementService.RUBRIQUES_SJ)
                | Q(
                    rubrique__classification_metier__in={
                        RubriqueCaisse.ClassificationMetier.CHARGE_EXPLOITATION,
                        RubriqueCaisse.ClassificationMetier.CHARGE_PERSONNELLE,
                    }
                )
            )
            .aggregate(total=Sum("montant"))["total"] or Decimal("0")
        )

        return total

    # ------------------------------------------------------------------
    # Contre-vérification : FR = TVMS + TSC + TSCl - TSCF
    # ------------------------------------------------------------------
    @staticmethod
    def compute_contreverification():
        """Contre-vérification FC (pour compatibilité historique)."""
        detail = FondsRoulementService.compute_contreverification_detail()
        return detail["tvms_fc"] + detail["tsc"] + detail["tscl"] - detail["tscf"]

    @staticmethod
    def compute_contreverification_usd():
        """Contre-vérification USD (nouvelle valeur de référence)."""
        detail = FondsRoulementService.compute_contreverification_detail()
        return detail["total_usd"]

    @staticmethod
    def compute_contreverification_detail():
        tvms_fc, tvms_usd = FondsRoulementService._compute_tvms()
        tsc = FondsRoulementService._compute_tsc()
        tsc_usd = FondsRoulementService._compute_tsc_usd()
        tscl = FondsRoulementService._compute_tscl()
        tscl_usd = FondsRoulementService._compute_tscl_usd()
        tscf = FondsRoulementService._compute_tscf()
        tscf_usd = FondsRoulementService._compute_tscf_usd()
        return {
            "tvms_fc": tvms_fc,
            "tvms_usd": tvms_usd,
            "tsc": tsc,
            "tsc_usd": tsc_usd,
            "tscl": tscl,
            "tscl_usd": tscl_usd,
            "tscf": tscf,
            "tscf_usd": tscf_usd,
            "total_fc": tvms_fc + tsc + tscl - tscf,
            "total_usd": tvms_usd + tsc_usd + tscl_usd - tscf_usd,
        }

    @staticmethod
    def _compute_tvms():
        """Valeur totale des marchandises en stock au prix de vente (FC et USD)."""
        from produits.models import Stock

        taux = FondsRoulementService._get_taux()

        stocks = (
            Stock.objects
            .select_related("article")
            .filter(qte__gt=0)
        )

        total_fc = Decimal("0")
        total_usd = Decimal("0")
        for s in stocks:
            prix = s.article.prix_vente
            if s.article.devise == "$":
                total_fc += prix * taux * s.qte
                total_usd += prix * s.qte
            else:
                total_fc += prix * s.qte
                if taux:
                    total_usd += (prix * s.qte) / taux

        # Retourne un tuple (fc, usd) pour permettre la sauvegarde des deux valeurs
        return total_fc, total_usd

    @staticmethod
    def _compute_tsc():
        """Somme des soldes de fermeture les plus récents par caisse (FC)."""
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
    def _compute_tsc_usd():
        """Somme des soldes de fermeture les plus récents par caisse (USD)."""
        from patrimoine.models import SnapshotJournalier
        from caisse.models import Caisse
        from parametres.models import get_taux_usd_cdf
        from decimal import Decimal
        
        taux = Decimal(str(get_taux_usd_cdf()))
        total = Decimal("0")
        
        for caisse in Caisse.objects.all():
            dernier = (
                SnapshotJournalier.objects
                .filter(caisse=caisse)
                .order_by("-date")
                .first()
            )
            if dernier:
                # Utiliser la valeur USD du snapshot si disponible, sinon convertir
                if dernier.solde_fermeture_usd:
                    total += dernier.solde_fermeture_usd
                elif taux:
                    total += dernier.solde_fermeture / taux

        return total

    @staticmethod
    def _compute_tscl():
        """Somme des soldes des comptes clients (créances) en FC (historique)."""
        from clients.models import Client
        total_fc = sum((c.solde_fc() or Decimal("0")) for c in Client.objects.all())
        return total_fc

    @staticmethod
    def _compute_tscf():
        """Somme des soldes des comptes fournisseurs (dettes) en FC (historique)."""
        from fournisseurs.models import Fournisseur
        total_fc = sum((f.solde_fc() or Decimal("0")) for f in Fournisseur.objects.all())
        return total_fc

    @staticmethod
    def _compute_tscl_usd():
        """Somme des soldes des comptes clients (créances) en USD (nouvelle référence)."""
        from clients.models import Client
        total_usd = sum((c.solde() or Decimal("0")) for c in Client.objects.all())
        return total_usd

    @staticmethod
    def _compute_tscf_usd():
        """Somme des soldes des comptes fournisseurs (dettes) en USD (nouvelle référence)."""
        from fournisseurs.models import Fournisseur
        total_usd = sum((f.solde() or Decimal("0")) for f in Fournisseur.objects.all())
        return total_usd

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
        fr_calcule = FondsRoulementService.compute_contreverification()
        ecart = fr_final - fr_calcule

        # Dual currency: calculer les valeurs USD
        taux = FondsRoulementService._get_taux()
        taux_jour = Decimal(str(taux)) if taux else None
        fr_initial_usd = (fr_initial / taux) if taux else None
        ej_usd = (ej / taux) if taux else None
        sj_usd = (sj / taux) if taux else None
        fr_final_usd = (fr_final / taux) if taux else None

        FondsRoulementSnapshot.objects.update_or_create(
            date=date,
            defaults={
                "fr_initial": fr_initial,
                "ej": ej,
                "sj": sj,
                "fr_final": fr_final,
                "fr_calcule": fr_calcule,
                "ecart": ecart,
                "taux_jour": taux_jour,
                "fr_initial_usd": fr_initial_usd,
                "ej_usd": ej_usd,
                "sj_usd": sj_usd,
                "fr_final_usd": fr_final_usd,
            }
        )
