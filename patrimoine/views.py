from collections import defaultdict
from users.permissions import RoleRequiredMixin, ROLE_ADMIN
from django.views.generic import ListView, TemplateView
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now as tz_now
from django.core.paginator import Paginator
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.timezone import now
from django.db.models import Sum, Count
import calendar
import datetime
from patrimoine.models import SnapshotJournalier, ResultatApprovisionnementSnapshot, ResultatJournalier, ResultatMensuel
from caisse.models import (MouvementCaisse, RubriqueCaisse, SousRubriqueCaisse, MouvementCaisseChargesExploitation,
                           MouvementCaisseChargesPersonnelles)
from patrimoine.services import JournalTransactionService, SnapshotService


"""
class JournalTransactionsView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    # permission_required = "finances.view_mouvementcaisse"
    model = MouvementCaisse
    template_name = "patrimoine/journal_transactions.html"
    paginate_by = 50

    def get_base_queryset(self):
        qs = (
            MouvementCaisse.objects
            .select_related(
                "caisse",
                "rubrique",
                "effectue_par"
            )
            .order_by("-date_mouvement")
        )

        # période par défaut : mois en cours
        mois = int(self.request.GET.get("mois", now().month))
        annee = int(self.request.GET.get("annee", now().year))

        qs = qs.filter(
            date_mouvement__month=mois,
            date_mouvement__year=annee
        )

        # filtres optionnels
        caisse = self.request.GET.get("caisse")
        if caisse:
            qs = qs.filter(caisse__caisse_id=caisse)

        rubrique = self.request.GET.get("rubrique")
        if rubrique:
            qs = qs.filter(rubrique_id=rubrique)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base_qs = self.get_base_queryset()

        entrees = base_qs.filter(type_mouvement="ENTREE")
        sorties = base_qs.filter(type_mouvement="SORTIE")

        total_entrees = entrees.aggregate(total=Sum("montant"))["total"] or 0
        total_sorties = sorties.aggregate(total=Sum("montant"))["total"] or 0
        solde = total_entrees - total_sorties

        ctx.update({
            "entrees": entrees,
            "sorties": sorties,

            "total_entrees": total_entrees,
            "total_sorties": total_sorties,
            "solde": solde,

            "mois": self.request.GET.get("mois", now().month),
            "annee": self.request.GET.get("annee", now().year),
            "dashboard_section": "journal",
        })

        return ctx
"""

class JournalTransactionsView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = "patrimoine/journal_transactions.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        today = datetime.date.today()
        debut_str = self.request.GET.get("debut")
        fin_str = self.request.GET.get("fin")

        if debut_str and fin_str:
            try:
                date_debut = datetime.date.fromisoformat(debut_str)
                date_fin = datetime.date.fromisoformat(fin_str)
            except ValueError:
                date_debut = today.replace(day=1)
                _, last_day = calendar.monthrange(today.year, today.month)
                date_fin = today.replace(day=last_day)
        else:
            date_debut = today.replace(day=1)
            _, last_day = calendar.monthrange(today.year, today.month)
            date_fin = today.replace(day=last_day)

        debut_str = date_debut.strftime("%Y-%m-%d")
        fin_str = date_fin.strftime("%Y-%m-%d")

        journal = JournalTransactionService.get_lines(date_debut, date_fin)

        # Filtres optionnels
        type_filter = self.request.GET.get("type", "")
        if type_filter in ("ENTREE", "SORTIE"):
            journal = [i for i in journal if i.type_mouvement == type_filter]

        q = self.request.GET.get("q", "").strip().lower()
        if q:
            journal = [
                i for i in journal
                if q in i.motif.lower() or q in i.rubrique_nom.lower() or q in i.caisse.lower()
            ]

        all_entrees = [i for i in journal if i.type_mouvement == "ENTREE"]
        all_sorties = [i for i in journal if i.type_mouvement == "SORTIE"]
        total_entrees = sum(i.montant for i in all_entrees)
        total_sorties = sum(i.montant for i in all_sorties)

        # Pagination : 50 lignes par page, paginées séparément par colonne
        page_e = int(self.request.GET.get("page_e", 1))
        page_s = int(self.request.GET.get("page_s", 1))

        paginateur_e = Paginator(all_entrees, 50)
        paginateur_s = Paginator(all_sorties, 50)

        entrees_page = paginateur_e.get_page(page_e)
        sorties_page = paginateur_s.get_page(page_s)

        ctx.update({
            "entrees": entrees_page,
            "sorties": sorties_page,
            "paginateur_e": paginateur_e,
            "paginateur_s": paginateur_s,
            "total_entrees": total_entrees,
            "total_sorties": total_sorties,
            "solde": total_entrees - total_sorties,
            "debut": debut_str,
            "fin": fin_str,
            "type_filter": type_filter,
            "q": self.request.GET.get("q", ""),
            "dashboard_section": "journal",
        })

        return ctx


class CalendrierFinancierView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = "patrimoine/calendrier_financier.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        today = now().date()
        mois = int(self.request.GET.get("mois", today.month))
        annee = int(self.request.GET.get("annee", today.year))

        # bornes du mois
        first_day = datetime.date(annee, mois, 1)
        _, last_day_num = calendar.monthrange(annee, mois)
        last_day = datetime.date(annee, mois, last_day_num)

        # snapshots du mois indexés par date (agrégés toutes caisses confondues)
        daily_agg = (
            SnapshotJournalier.objects
            .filter(date__range=(first_day, last_day))
            .values('date')
            .annotate(
                total_entrees=Sum('total_entrees'),
                total_sorties=Sum('total_sorties'),
                solde_fermeture=Sum('solde_fermeture'),
            )
        )
        snapshots = {s['date']: s for s in daily_agg}

        # Résultats d'approvisionnement par jour (source principale de revenus)
        appro_par_jour = SnapshotService.get_appro_par_jour(first_day, last_day)

        # générateur calendrier (lundi -> dimanche)
        cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        weeks = []

        for week in cal.monthdatescalendar(annee, mois):
            week_days = []
            for day in week:
                if day.month != mois:
                    week_days.append(None)
                    continue

                snap = snapshots.get(day)
                entrees_caisse = snap['total_entrees'] if snap else 0
                sorties = snap['total_sorties'] if snap else 0
                entrees = entrees_caisse + (appro_par_jour.get(day) or 0)
                solde = entrees - sorties

                week_days.append({
                    "date": day,
                    "numero": day.day,
                    "entrees": entrees,
                    "sorties": sorties,
                    "solde": solde,
                    "is_today": day == today,
                })

            weeks.append(week_days)

        # navigation mois
        prev_month = mois - 1 or 12
        prev_year = annee - 1 if mois == 1 else annee

        next_month = mois + 1 if mois < 12 else 1
        next_year = annee + 1 if mois == 12 else annee

        days = "Lundi Mardi Mercredi Jeudi Vendredi Samedi Dimanche".split()

        snapshots = SnapshotJournalier.objects.filter(
            date__range=(first_day, last_day)
        ).order_by("date")

        monthly_aggregates = snapshots.aggregate(
            total_entrees=Sum("total_entrees"),
            total_sorties=Sum("total_sorties"),
        )

        first_snapshot = snapshots.first()
        last_snapshot = snapshots.last()

        total_appro_mois = SnapshotService.get_appro_total(first_day, last_day)

        ctx.update({
            "days": days,
            "weeks": weeks,
            "mois": mois,
            "annee": annee,
            "mois_label": first_day.strftime("%B %Y").capitalize(),
            "prev": {"mois": prev_month, "annee": prev_year},
            "next": {"mois": next_month, "annee": next_year},

            "total_entrees_mois": (monthly_aggregates["total_entrees"] or 0) + total_appro_mois,
            "total_sorties_mois": monthly_aggregates["total_sorties"] or 0,
            "solde_mois": last_snapshot.solde_fermeture if last_snapshot else 0,

            "dashboard_section": "calendrier",
        })

        return ctx


class StatistiquesFinancieresView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = "patrimoine/statistiques.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        today = datetime.date.today()
        debut_str = self.request.GET.get("debut")
        fin_str   = self.request.GET.get("fin")

        if debut_str and fin_str:
            try:
                date_debut = datetime.date.fromisoformat(debut_str)
                date_fin   = datetime.date.fromisoformat(fin_str)
            except ValueError:
                date_debut = today.replace(day=1)
                _, last_day = calendar.monthrange(today.year, today.month)
                date_fin = today.replace(day=last_day)
        else:
            date_debut = today.replace(day=1)
            _, last_day = calendar.monthrange(today.year, today.month)
            date_fin = today.replace(day=last_day)

        debut_str = date_debut.strftime("%Y-%m-%d")
        fin_str   = date_fin.strftime("%Y-%m-%d")

        base_qs = MouvementCaisse.objects.filter(
            date_mouvement__date__range=(date_debut, date_fin)
        ).exclude(rubrique__nom__in=SnapshotService.EXCLUDED_RUBRIQUES)

        # =========================
        # TOTAUX
        # =========================
        total_entrees_caisse = (
            base_qs.filter(type_mouvement="ENTREE")
            .aggregate(total=Sum("montant"))["total"] or 0
        )

        total_sorties = (
            base_qs.filter(type_mouvement="SORTIE")
            .aggregate(total=Sum("montant"))["total"] or 0
        )

        # Les résultats d'approvisionnement sont la principale source de revenus :
        # ils n'apparaissent pas dans MouvementCaisse mais dans leur propre table.
        appro_total = SnapshotService.get_appro_total(date_debut, date_fin)
        total_entrees = total_entrees_caisse + appro_total

        solde = total_entrees - total_sorties

        # =========================
        # RÉPARTITIONS
        # =========================
        def repartition(type_mvt, total):
            qs = (
                base_qs.filter(type_mouvement=type_mvt)
                .values("rubrique__nom")
                .annotate(montant=Sum("montant"))
                .order_by("-montant")
            )

            result = []
            for r in qs:
                pourcentage = (float(r["montant"]) / float(total) * 100) if total else 0
                result.append({
                    "label": r["rubrique__nom"],
                    "montant": float(r["montant"]),
                    "pourcentage": round(pourcentage, 1)
                })
            return result

        repartition_entrees = repartition("ENTREE", total_entrees)

        # Ajouter la ligne Approvisionnement à la répartition des entrées
        if appro_total > 0:
            pourcentage_appro = round(float(appro_total) / float(total_entrees) * 100, 1) if total_entrees else 0
            repartition_entrees.append({
                "label": "Approvisionnement",
                "montant": float(appro_total),
                "pourcentage": pourcentage_appro,
            })
            repartition_entrees.sort(key=lambda x: x["montant"], reverse=True)

        repartition_sorties = repartition("SORTIE", total_sorties)

        # =========================
        # CONTEXT
        # =========================
        ctx.update({
            "debut": debut_str,
            "fin": fin_str,
            "total_entrees": total_entrees,
            "total_sorties": total_sorties,
            "solde": solde,
            "repartition_entrees": repartition_entrees,
            "repartition_sorties": repartition_sorties,
            "dashboard_section": "statistiques",
            "devise": "FC",
        })

        return ctx


class ResultatsView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = "patrimoine/resultats.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        today = datetime.date.today()
        debut_str = self.request.GET.get("debut")

        # Dériver mois/année depuis la date de début ; recadrer sur le mois entier
        if debut_str:
            try:
                date_debut = datetime.date.fromisoformat(debut_str)
            except ValueError:
                date_debut = today.replace(day=1)
        else:
            date_debut = today.replace(day=1)

        mois  = date_debut.month
        annee = date_debut.year
        _, last_day = calendar.monthrange(annee, mois)
        date_debut = datetime.date(annee, mois, 1)
        date_fin   = datetime.date(annee, mois, last_day)

        debut_str = date_debut.strftime("%Y-%m-%d")
        fin_str   = date_fin.strftime("%Y-%m-%d")

        # --- SOURCES (agrégats persistés) ---
        resultat_brut, chiffre_affaires = self.get_resultat_brut(mois, annee)

        charges = ResultatApprovisionnementSnapshot.objects.filter(
            date__month=mois,
            date__year=annee,
        ).aggregate(
            cout_achat=Sum("cout_achat"),
            frais_achat=Sum("frais_achat")
        )

        charges_exploitation_details = self.get_charges_exploitation(mois, annee)
        charges_exploitation_total = sum(i["total"] for i in charges_exploitation_details)
        charges_personnelles, charges_personnelles_detail = self.get_charges_personnelles(mois, annee)

        # --- CASCADE ---
        cout_achat = charges["cout_achat"] or 0
        frais_achat = charges["frais_achat"] or 0
        total_cout_achat = cout_achat + frais_achat
        resultat_net_exploitation = resultat_brut - charges_exploitation_total
        resultat_net = resultat_net_exploitation - charges_personnelles

        # --- POURCENTAGES ---
        from decimal import Decimal
        marge_pct = round(float(resultat_brut) / float(chiffre_affaires) * 100, 1) if chiffre_affaires else 0
        rne_pct = round(float(resultat_net_exploitation) / float(resultat_brut) * 100, 1) if resultat_brut else 0

        sous_rubriques = SousRubriqueCaisse.objects.filter(rubrique__nom="Charges exploitation")

        ctx.update({
            "mois": mois,
            "annee": annee,
            "debut": debut_str,
            "fin": fin_str,

            "resultat_brut": resultat_brut,
            "chiffre_affaires": chiffre_affaires,
            "cout_achat": cout_achat,
            "frais_achat": frais_achat,
            "total_cout_achat": total_cout_achat,
            "marge_pct": marge_pct,

            "charges_exploitation": charges_exploitation_details,
            "total_charges_exploitation": charges_exploitation_total,
            "charges_personnelles": charges_personnelles,
            "charges_personnelles_detail": charges_personnelles_detail,
            "rne_pct": rne_pct,

            "resultat_net_exploitation": resultat_net_exploitation,
            "resultat_net": resultat_net,

            "sous_rubriques": sous_rubriques,
        })

        return ctx

    def get_resultat_brut(self, mois, annee):
        """
        Lecture de l’agrégat mensuel des résultats journaliers
        """
        obj = ResultatMensuel.objects.filter(
                mois=mois,
                annee=annee
        ).first()

        if not obj:
            return 0, 0

        return obj.resultat_brut, obj.chiffre_affaires

    def get_charges_exploitation(self, mois, annee):
        """
        Dépenses catégorisées EXPLOITATION
        """
        linked_qs = (
            MouvementCaisseChargesExploitation.objects
            .filter(
                mouvement_caisse__date_mouvement__month=mois,
                mouvement_caisse__date_mouvement__year=annee,
                mouvement_caisse__type_mouvement="SORTIE",
            )
            .values("sous_rubrique__nom")
            .annotate(total=Sum("mouvement_caisse__montant"))
        )
        linked_ids = list(
            MouvementCaisseChargesExploitation.objects
            .filter(
                mouvement_caisse__date_mouvement__month=mois,
                mouvement_caisse__date_mouvement__year=annee,
                mouvement_caisse__type_mouvement="SORTIE",
            )
            .values_list("mouvement_caisse_id", flat=True)
        )

        direct_qs = (
            MouvementCaisse.objects
            .filter(
                date_mouvement__month=mois,
                date_mouvement__year=annee,
                type_mouvement="SORTIE",
                rubrique__classification_metier=(
                    RubriqueCaisse.ClassificationMetier.CHARGE_EXPLOITATION
                ),
            )
            .exclude(id__in=linked_ids)
            .values("rubrique__nom")
            .annotate(total=Sum("montant"))
        )

        totals = defaultdict(int)
        for item in linked_qs:
            totals[item["sous_rubrique__nom"]] += item["total"] or 0
        for item in direct_qs:
            totals[item["rubrique__nom"]] += item["total"] or 0

        return [
            {"sous_rubrique__nom": label, "total": total}
            for label, total in sorted(
                totals.items(),
                key=lambda entry: entry[1],
                reverse=True,
            )
        ]

    def get_charges_personnelles(self, mois, annee):
        """
        Dépenses catégorisées PERSONNEL — retourne (total, detail)
        """
        linked_qs = list(
            MouvementCaisseChargesPersonnelles.objects
            .filter(
                mouvement_caisse__date_mouvement__month=mois,
                mouvement_caisse__date_mouvement__year=annee,
                mouvement_caisse__type_mouvement="SORTIE",
            )
            .values("sous_rubrique__nom")
            .annotate(total=Sum("mouvement_caisse__montant"))
        )
        linked_ids = list(
            MouvementCaisseChargesPersonnelles.objects
            .filter(
                mouvement_caisse__date_mouvement__month=mois,
                mouvement_caisse__date_mouvement__year=annee,
                mouvement_caisse__type_mouvement="SORTIE",
            )
            .values_list("mouvement_caisse_id", flat=True)
        )

        direct_qs = list(
            MouvementCaisse.objects
            .filter(
                date_mouvement__month=mois,
                date_mouvement__year=annee,
                type_mouvement="SORTIE",
                rubrique__classification_metier=(
                    RubriqueCaisse.ClassificationMetier.CHARGE_PERSONNELLE
                ),
            )
            .exclude(id__in=linked_ids)
            .values("rubrique__nom")
            .annotate(total=Sum("montant"))
        )

        totals = defaultdict(int)
        for item in linked_qs:
            totals[item["sous_rubrique__nom"]] += item["total"] or 0
        for item in direct_qs:
            totals[item["rubrique__nom"]] += item["total"] or 0

        detail = [
            {"sous_rubrique__nom": label, "total": total}
            for label, total in sorted(
                totals.items(),
                key=lambda entry: entry[1],
                reverse=True,
            )
        ]
        total = sum(item["total"] for item in detail) if detail else 0
        return total, detail


class SuiviCapitauxView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = "patrimoine/suivi_capitaux.html"

    def get_context_data(self, **kwargs):
        import json
        from decimal import Decimal
        from patrimoine.models import FondsRoulementSnapshot
        from patrimoine.services.fonds_roulement_service import FondsRoulementService
        from creanciers.models import Creancier, Debiteur

        ctx = super().get_context_data(**kwargs)

        today = datetime.date.today()
        debut_str = self.request.GET.get("debut")
        fin_str = self.request.GET.get("fin")

        if debut_str and fin_str:
            try:
                date_debut = datetime.date.fromisoformat(debut_str)
                date_fin = datetime.date.fromisoformat(fin_str)
            except ValueError:
                date_debut = today.replace(day=1)
                _, last_day_num = calendar.monthrange(today.year, today.month)
                date_fin = today.replace(day=last_day_num)
        else:
            date_debut = today.replace(day=1)
            _, last_day_num = calendar.monthrange(today.year, today.month)
            date_fin = today.replace(day=last_day_num)

        debut_str = date_debut.strftime("%Y-%m-%d")
        fin_str = date_fin.strftime("%Y-%m-%d")

        # Historique FR de la période sélectionnée (dépend du filtre)
        historique = list(
            FondsRoulementSnapshot.objects
            .filter(date__range=(date_debut, date_fin))
            .order_by("date")
        )

        # KPI : dernier snapshot GLOBAL (instant T, indépendant du filtre)
        dernier_global = FondsRoulementSnapshot.objects.order_by("-date").first()
        fr_final = dernier_global.fr_final if dernier_global else Decimal("0")
        fr_contreverif = dernier_global.fr_contreverif if dernier_global else Decimal("0")
        ecart = dernier_global.ecart if dernier_global else Decimal("0")

        # Contre-vérification live (composantes détaillées, instant T)
        contreverif_detail = FondsRoulementService.compute_contreverification_detail()

        # Fonds Propre = FR + total débiteurs - total créanciers (instant T)
        total_debiteurs = sum(
            (d.solde() or Decimal("0")) for d in Debiteur.objects.all()
        )
        total_creanciers = sum(
            (c.solde() or Decimal("0")) for c in Creancier.objects.all()
        )
        fonds_propre = fr_final + total_debiteurs - total_creanciers

        # Données graphique Chart.js (dépend du filtre)
        chart_labels = [s.date.strftime("%d/%m") for s in historique]
        chart_data = [float(s.fr_final) for s in historique]

        ctx.update({
            "debut": debut_str,
            "fin": fin_str,

            # KPI tiles (instant T)
            "fr_final": fr_final,
            "fr_contreverif": fr_contreverif,
            "ecart": ecart,
            "fonds_propre": fonds_propre,

            # Historique tableau (filtré)
            "historique": historique,

            # Contre-vérification détail (instant T)
            "contreverif": contreverif_detail,

            # Fonds Propre détail (instant T)
            "total_debiteurs": total_debiteurs,
            "total_creanciers": total_creanciers,

            # Graphique (filtré)
            "chart_labels": chart_labels,
            "chart_data": chart_data,
        })
        return ctx



class PatrimoineView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'patrimoine/patrimoine.html'

    def get_context_data(self, **kwargs):
        from patrimoine.models import FondsRoulementSnapshot
        from creanciers.models import Creancier, Debiteur
        from decimal import Decimal

        ctx = super().get_context_data(**kwargs)

        today = datetime.date.today()
        date_debut = today.replace(day=1)
        _, last_day = calendar.monthrange(today.year, today.month)
        date_fin = today.replace(day=last_day)

        mois_label = date_debut.strftime("%B %Y").capitalize()

        base_qs = MouvementCaisse.objects.filter(
            date_mouvement__date__range=(date_debut, date_fin)
        ).exclude(rubrique__nom__in={"clients", "fournisseurs"})

        entrees_agg = base_qs.filter(type_mouvement="ENTREE").aggregate(
            total=Sum("montant"), nb=Count("id")
        )
        sorties_agg = base_qs.filter(type_mouvement="SORTIE").aggregate(
            total=Sum("montant"), nb=Count("id")
        )

        # Résultats bruts d'approvisionnement (entrées du périmètre patrimoine)
        appro_entrees = ResultatApprovisionnementSnapshot.objects.filter(
            date__range=(date_debut, date_fin)
        ).aggregate(total=Sum("resultat_brut"))["total"] or Decimal("0")

        total_entrees = (entrees_agg["total"] or Decimal("0")) + appro_entrees
        total_sorties = sorties_agg["total"] or Decimal("0")
        nb_entrees = entrees_agg["nb"] or 0
        nb_sorties = sorties_agg["nb"] or 0
        resultat_net = total_entrees - total_sorties

        dernier_snap = FondsRoulementSnapshot.objects.order_by("-date").first()
        solde_global = dernier_snap.fr_final if dernier_snap else Decimal("0")

        # Fonds Propre = FR + Débiteurs - Créanciers (instant T)
        total_debiteurs = sum((d.solde() or Decimal("0")) for d in Debiteur.objects.all())
        total_creanciers = sum((c.solde() or Decimal("0")) for c in Creancier.objects.all())
        fonds_propre = solde_global + total_debiteurs - total_creanciers

        ctx.update({
            "mois_label": mois_label,
            "total_entrees": total_entrees,
            "total_sorties": total_sorties,
            "nb_entrees": nb_entrees,
            "nb_sorties": nb_sorties,
            "resultat_net": resultat_net,
            "solde_global": solde_global,
            "fonds_propre": fonds_propre,
            "total_debiteurs": total_debiteurs,
            "total_creanciers": total_creanciers,
        })
        return ctx


class PatrimoineExportPDFView(RoleRequiredMixin, View):

    allowed_roles = [ROLE_ADMIN]
    def get(self, request):
        today = datetime.date.today()
        debut_str = request.GET.get("debut")
        fin_str = request.GET.get("fin")

        if debut_str and fin_str:
            try:
                first_day = datetime.date.fromisoformat(debut_str)
                last_day = datetime.date.fromisoformat(fin_str)
            except ValueError:
                first_day = today.replace(day=1)
                _, last_day_num = calendar.monthrange(today.year, today.month)
                last_day = today.replace(day=last_day_num)
        else:
            first_day = today.replace(day=1)
            _, last_day_num = calendar.monthrange(today.year, today.month)
            last_day = today.replace(day=last_day_num)

        from patrimoine.services.pdf_service import PatrimoinePDFService
        return PatrimoinePDFService.generate(first_day, last_day)


class ValiderFRView(RoleRequiredMixin, View):
    allowed_roles = [ROLE_ADMIN]
    """
    Acte métier : valide (ou dévalide) un FondsRoulementSnapshot.
    POST /patrimoine/capitaux/<id>/valider/
    """

    def post(self, request, pk):
        from patrimoine.models import FondsRoulementSnapshot
        snap = get_object_or_404(FondsRoulementSnapshot, pk=pk)

        if snap.valide:
            # Toggle : dévalider
            snap.valide = False
            snap.valide_par = None
            snap.valide_le = None
        else:
            snap.valide = True
            snap.valide_par = request.user
            snap.valide_le = tz_now()

        snap.save(update_fields=["valide", "valide_par", "valide_le"])

        referer = request.META.get("HTTP_REFERER", "")
        return redirect(referer or "patrimoine_capitaux")
