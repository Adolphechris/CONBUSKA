from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.timezone import now
from django.db.models import Sum
import calendar
from datetime import date
from patrimoine.models import SnapshotJournalier, ResultatApprovisionnementSnapshot, ResultatJournalier, ResultatMensuel
from caisse.models import (MouvementCaisse, SousRubriqueCaisse, MouvementCaisseChargesExploitation,
                           MouvementCaisseChargesPersonnelles)


class JournalTransactionsView(LoginRequiredMixin, TemplateView):
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


class CalendrierFinancierView(LoginRequiredMixin, TemplateView):
    template_name = "patrimoine/calendrier_financier.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        today = now().date()
        mois = int(self.request.GET.get("mois", today.month))
        annee = int(self.request.GET.get("annee", today.year))

        # bornes du mois
        first_day = date(annee, mois, 1)
        _, last_day_num = calendar.monthrange(annee, mois)
        last_day = date(annee, mois, last_day_num)

        # snapshots du mois indexés par date
        snapshots = {
            s.date: s
            for s in SnapshotJournalier.objects.filter(
                date__range=(first_day, last_day)
            )
        }

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
                entrees = snap.total_entrees if snap else 0
                sorties = snap.total_sorties if snap else 0
                solde = snap.solde_fermeture if snap else (entrees - sorties)

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

        ctx.update({
            "days": days,
            "weeks": weeks,
            "mois": mois,
            "annee": annee,
            "mois_label": first_day.strftime("%B %Y").capitalize(),
            "prev": {"mois": prev_month, "annee": prev_year},
            "next": {"mois": next_month, "annee": next_year},

            "total_entrees_mois": monthly_aggregates["total_entrees"] or 0,
            "total_sorties_mois": monthly_aggregates["total_sorties"] or 0,
            "solde_mois": last_snapshot.solde_fermeture if last_snapshot else 0,

            "dashboard_section": "calendrier",
        })

        return ctx


class StatistiquesFinancieresView(LoginRequiredMixin, TemplateView):
    template_name = "patrimoine/statistiques.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        mois = int(self.request.GET.get("mois", now().month))
        annee = int(self.request.GET.get("annee", now().year))

        base_qs = MouvementCaisse.objects.filter(
            date_mouvement__month=mois,
            date_mouvement__year=annee
        )

        # =========================
        # TOTAUX
        # =========================
        total_entrees = (
            base_qs.filter(type_mouvement="ENTREE")
            .aggregate(total=Sum("montant"))["total"] or 0
        )

        total_sorties = (
            base_qs.filter(type_mouvement="SORTIE")
            .aggregate(total=Sum("montant"))["total"] or 0
        )

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
                pourcentage = (r["montant"] / total * 100) if total else 0
                result.append({
                    "label": r["rubrique__nom"],
                    "montant": r["montant"],
                    "pourcentage": round(pourcentage, 1)
                })
            return result

        repartition_entrees = repartition("ENTREE", total_entrees)
        repartition_sorties = repartition("SORTIE", total_sorties)

        # =========================
        # CONTEXT
        # =========================
        ctx.update({
            "mois": mois,
            "annee": annee,
            "total_entrees": total_entrees,
            "total_sorties": total_sorties,
            "solde": solde,
            "repartition_entrees": repartition_entrees,
            "repartition_sorties": repartition_sorties,
            "dashboard_section": "statistiques",
            "devise": "FC",
        })

        return ctx


class ResultatsView(LoginRequiredMixin, TemplateView):
    template_name = "patrimoine/resultats.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        mois = int(self.request.GET.get("mois", now().month))
        annee = int(self.request.GET.get("annee", now().year))

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
        charges_personnelles = self.get_charges_personnelles(mois, annee)

        # --- CASCADE ---
        resultat_net_exploitation = resultat_brut - charges_exploitation_total
        resultat_net = resultat_net_exploitation - charges_personnelles

        sous_rubriques = SousRubriqueCaisse.objects.filter(rubrique__nom="Charges exploitation")

        ctx.update({
            "mois": mois,
            "annee": annee,

            "resultat_brut": resultat_brut,
            "chiffre_affaires": chiffre_affaires,
            "cout_achat": charges["cout_achat"] or 0,
            "frais_achat": charges["frais_achat"] or 0,

            "charges_exploitation": charges_exploitation_details,
            "total_charges_exploitation": charges_exploitation_total,
            "charges_personnelles": charges_personnelles,

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
        charges_exploitation_detail = (
            MouvementCaisseChargesExploitation.objects
            .filter(
                mouvement_caisse__date_mouvement__month=mois,
                mouvement_caisse__date_mouvement__year=annee,
            )
            .values("sous_rubrique__nom")
            .annotate(total=Sum("mouvement_caisse__montant"))
        )
        return charges_exploitation_detail

    def get_charges_personnelles(self, mois, annee):
        """
        Dépenses catégorisées PERSONNEL
        """
        charges_personnelles = (
               MouvementCaisseChargesPersonnelles.objects
               .filter(
                   mouvement_caisse__date_mouvement__month=mois,
                   mouvement_caisse__date_mouvement__year=annee,
               )
               .aggregate(total=Sum("mouvement_caisse__montant"))
        )["total"] or 0
        return charges_personnelles


class SuiviCapitauxView(LoginRequiredMixin, TemplateView):
    template_name = "patrimoine/suivi_capitaux.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        date_params = self.request.GET.get("date", now().date())

        # fr = FondsRoulementSnapshot.objects.filter(date=date).first()
        # fp = FondsPropreSnapshot.objects.filter(date=date).first()x

        fr = 0
        fp = 0

        ctx.update({
            "date": date_params,
            "fr": fr,
            "fp": fp,
        })
        return ctx



class PatrimoineView(LoginRequiredMixin, TemplateView):
    template_name = 'patrimoine/patrimoine.html'
