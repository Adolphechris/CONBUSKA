from users.permissions import RoleRequiredMixin, ROLE_ADMIN
import datetime
import logging

from django.db.models import DecimalField, F, Min, Sum
from django.db.models.functions import ExtractMonth
from django.http import JsonResponse
from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView, RedirectView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from approvisionnements.models import DetailsApprovisionnement
from factures.models import DetailsFacture, Facture
from parametres.models import Parametre
from utils.pdf_generator import DocumentGenerator

logger = logging.getLogger(__name__)


class RapportVenteView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'rapports/rapport_vente.html'

    def _get_periode(self):
        today = timezone.now().date()
        try:
            debut = datetime.date.fromisoformat(self.request.GET.get('debut', ''))
        except ValueError:
            debut = today
        try:
            fin = datetime.date.fromisoformat(self.request.GET.get('fin', ''))
        except ValueError:
            fin = today
        return debut, fin

    def get_mois(self):
        return ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    @staticmethod
    def ventes_par_mois():
        current_year = timezone.now().year
        return (Facture.objects
                .filter(date_facture__year=current_year)
                .annotate(mois=ExtractMonth('date_facture'))
                .values('mois')
                .annotate(
                    total_vendu=Sum(
                        F('facture_details__qte') * F('facture_details__prix'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ) - Sum('remise')
                )
                .order_by('mois'))

    def get_ventes_chart(self):
        data = [0] * 12
        for item in self.ventes_par_mois():
            mois = item['mois']
            total = item['total_vendu'] or 0
            data[mois - 1] = float(total)
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        debut, fin = self._get_periode()
        ventes = Facture.objects.ventes_journalieres(debut, fin)
        total_ventes = sum(v['total_vendu'] or 0 for v in ventes)

        context['debut'] = debut.isoformat()
        context['fin'] = fin.isoformat()
        context['total_ventes'] = total_ventes
        context['ventes'] = Facture.objects.ventes_journalieres(debut, fin)
        context['mois_labels'] = self.get_mois()
        context['chart_data'] = self.get_ventes_chart()
        return context


class RapportVenteDetailsView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'rapports/rapport_vente_details.html'

    def get_factures(self):
        factures_qs = Facture.objects.filter(date_facture=self.kwargs['date_facture'])
        return factures_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['factures'] = self.get_factures()
        return context


class RapportVenteDetailsFactureView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN]
    model = Facture
    template_name = 'rapports/rapport_vente_details_facture.html'

    def get_details_facture(self):
        details_facture = DetailsFacture.objects.filter(facture=self.kwargs['pk'])
        return details_facture

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['details_facture'] = self.get_details_facture()
        return context


class RapportResultatView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'rapports/rapport_resultat.html'

    def _get_periode(self):
        today = timezone.now().date()
        try:
            debut = datetime.date.fromisoformat(self.request.GET.get('debut', ''))
        except ValueError:
            debut = today.replace(day=1)
        try:
            fin = datetime.date.fromisoformat(self.request.GET.get('fin', ''))
        except ValueError:
            fin = today
        return debut, fin

    def _get_resultat_ventes(self, debut, fin):
        return (DetailsFacture.objects
                .filter(facture__date_facture__range=(debut, fin))
                .annotate(resultat=(F('prix') - F('article__prix_achat')) * F('qte'))
                .aggregate(total=Sum('resultat', output_field=DecimalField()))['total'] or 0)

    def _get_resultat_appros(self, debut, fin):
        """Résultat des appros validés : (prix_vente - cout_achat) * qte, itération Python."""
        qs = (DetailsApprovisionnement.objects
              .select_related('approvisionnement', 'article')
              .filter(
                  approvisionnement__valide=True,
                  approvisionnement__date_creation__date__range=(debut, fin),
              ))
        total = 0
        par_article = {}
        for d in qs:
            r = d.resultat
            total += r
            aid = d.article_id
            if aid not in par_article:
                par_article[aid] = {
                    'designation': d.article.designation,
                    'resultat': 0,
                }
            par_article[aid]['resultat'] += r
        return total, par_article

    def _get_resultat_par_article(self, debut, fin, total_global):
        """Résultat des appros par article avec % sur le total de référence."""
        _, par_article = self._get_resultat_appros(debut, fin)
        results = []
        for article_id, item in par_article.items():
            pct = (
                round(float(item['resultat']) / float(total_global) * 100, 2)
                if total_global
                else 0
            )
            results.append({
                'article_id': article_id,
                'designation': item['designation'],
                'resultat': item['resultat'],
                'pourcentage': pct,
            })
        results.sort(key=lambda item: item['resultat'], reverse=True)
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        debut, fin = self._get_periode()

        total_ventes = self._get_resultat_ventes(debut, fin)
        total_appros, _ = self._get_resultat_appros(debut, fin)
        total_global = total_appros

        articles = self._get_resultat_par_article(debut, fin, total_global)

        context.update({
            'debut': debut.isoformat(),
            'fin': fin.isoformat(),
            'total_ventes': total_ventes,
            'total_appros': total_appros,
            'total_global': total_global,
            'resultat_articles': articles,
            'chart_labels': [a['designation'] for a in articles[:10]],
            'chart_data': [float(a['resultat']) for a in articles[:10]],
        })
        return context


class RapportArticleView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'rapports/rapport_article.html'

    @staticmethod
    def _prix_fc(article, taux):
        """Prix de vente de l'article converti en FC."""
        if article.devise == '$':
            return float(article.prix_vente) * taux
        return float(article.prix_vente)

    def get_context_data(self, **kwargs):
        from produits.models import Stock as StockModel, MouvementStock
        from produits.models import Article
        from django.db.models.functions import TruncDate
        from parametres.models import get_taux_usd_cdf
        from collections import defaultdict

        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        debut_30j = today - datetime.timedelta(days=29)
        taux = get_taux_usd_cdf()

        # ── 1. Stock actuel (tous magasins) ──────────────────────────
        stock_actuel = {
            row['article_id']: row['qte']
            for row in StockModel.objects.values('article_id').annotate(qte=Sum('qte'))
        }

        # ── 2. Articles ayant du stock OU des ventes sur 30j ─────────
        aids_ventes = set(
            DetailsFacture.objects
            .filter(facture__date_facture__range=(debut_30j, today))
            .values_list('article_id', flat=True).distinct()
        )
        article_ids = set(stock_actuel.keys()) | aids_ventes
        articles = {a.pk: a for a in Article.objects.filter(pk__in=article_ids)}

        # ── 3. Valeur stock FC par article ────────────────────────────
        valeur_stock = {
            aid: stock_actuel.get(aid, 0) * self._prix_fc(articles[aid], taux)
            for aid in article_ids if aid in articles
        }
        total_valeur_stock = sum(valeur_stock.values())

        # ── 4. CA 30j par article (ORM) ───────────────────────────────
        ca_30j = {
            row['article_id']: float(row['ca'] or 0)
            for row in (DetailsFacture.objects
                        .filter(facture__date_facture__range=(debut_30j, today))
                        .values('article_id')
                        .annotate(ca=Sum(F('qte') * F('prix'),
                                         output_field=DecimalField())))
        }
        ca_total_30j = sum(ca_30j.values())

        # ── 5. Résultat 30j par article (ORM) ────────────────────────
        resultat_30j = {
            row['article_id']: float(row['res'] or 0)
            for row in (DetailsFacture.objects
                        .filter(facture__date_facture__range=(debut_30j, today))
                        .values('article_id')
                        .annotate(res=Sum(
                            (F('prix') - F('article__prix_achat')) * F('qte'),
                            output_field=DecimalField())))
        }
        resultat_total_30j = sum(resultat_30j.values())

        # ── 6. Moyenne journalière valeur stock (30 jours) ────────────
        # stock(D) = stock_actuel − cumul_delta(D+1..today)
        # delta(day) = IN(day) − OUT(day)
        delta_by_day = defaultdict(lambda: defaultdict(int))
        for row in (MouvementStock.objects
                    .filter(date_creation__date__range=(debut_30j, today))
                    .annotate(jour=TruncDate('date_creation'))
                    .values('article_id', 'jour', 'type')
                    .annotate(total=Sum('qte'))):
            day = row['jour']
            if hasattr(day, 'date'):
                day = day.date()
            if row['type'] == MouvementStock.IN:
                delta_by_day[row['article_id']][day] += row['total']
            else:
                delta_by_day[row['article_id']][day] -= row['total']

        # 30 jours du plus récent au plus ancien
        all_days = [today - datetime.timedelta(days=i) for i in range(30)]

        moy_stock_30j = {}
        for aid in article_ids:
            if aid not in articles:
                continue
            pv_fc = self._prix_fc(articles[aid], taux)
            qte_now = stock_actuel.get(aid, 0)
            deltas = delta_by_day.get(aid, {})
            cumul = 0
            total_val = 0
            for day in all_days:   # today → today-29
                total_val += max(0, qte_now - cumul) * pv_fc
                cumul += deltas.get(day, 0)
            moy_stock_30j[aid] = total_val / len(all_days)

        total_moy = sum(moy_stock_30j.values())

        # ── 7. Assemblage des lignes ──────────────────────────────────
        rows = []
        for aid in article_ids:
            a = articles.get(aid)
            if not a:
                continue
            val  = valeur_stock.get(aid, 0)
            ca   = ca_30j.get(aid, 0)
            res  = resultat_30j.get(aid, 0)
            moy  = moy_stock_30j.get(aid, 0)
            rows.append({
                'designation'  : a.designation,
                'valeur_stock' : round(val, 0),
                'pct_stock'    : round(val  / total_valeur_stock  * 100, 1) if total_valeur_stock  else 0,
                'ca_30j'       : round(ca,  0),
                'pct_ca'       : round(ca   / ca_total_30j        * 100, 1) if ca_total_30j        else 0,
                'resultat_30j' : round(res, 0),
                'pct_resultat' : round(res  / resultat_total_30j  * 100, 1) if resultat_total_30j  else 0,
                'moy_stock_30j': round(moy, 0),
                'pct_moy_stock': round(moy  / total_moy           * 100, 1) if total_moy           else 0,
            })

        rows.sort(key=lambda x: x['valeur_stock'], reverse=True)
        top10 = rows[:10]

        context.update({
            'total_valeur_stock' : round(total_valeur_stock, 0),
            'ca_total_30j'       : round(ca_total_30j, 0),
            'resultat_total_30j' : round(resultat_total_30j, 0),
            'nb_articles'        : len(rows),
            'articles_data'      : rows,
            'chart_labels'       : [r['designation'] for r in top10],
            'chart_valeur'       : [r['valeur_stock'] for r in top10],
            'chart_ca'           : [r['ca_30j'] for r in top10],
        })
        return context


class RapportCaisseView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'rapports/rapport_caisse.html'

    def _get_periode(self):
        today = timezone.now().date()
        try:
            debut = datetime.date.fromisoformat(self.request.GET.get('debut', ''))
        except ValueError:
            debut = today
        try:
            fin = datetime.date.fromisoformat(self.request.GET.get('fin', ''))
        except ValueError:
            fin = today
        return debut, fin

    def get_context_data(self, **kwargs):
        from caisse.models import MouvementCaisse, Caisse
        from patrimoine.models import SnapshotJournalier

        context = super().get_context_data(**kwargs)
        debut, fin = self._get_periode()

        base_qs = MouvementCaisse.objects.filter(
            date_mouvement__date__range=(debut, fin)
        ).select_related('caisse', 'caisse__caisse', 'rubrique', 'effectue_par')

        total_entrees = base_qs.filter(type_mouvement='ENTREE').aggregate(
            t=Sum('montant'))['t'] or 0
        total_sorties = base_qs.filter(type_mouvement='SORTIE').aggregate(
            t=Sum('montant'))['t'] or 0

        # Solde par caisse
        solde_par_caisse = []
        for caisse in Caisse.objects.all():
            snap = (SnapshotJournalier.objects
                    .filter(caisse=caisse, date__lte=fin)
                    .order_by('-date').first())
            entrees = base_qs.filter(
                caisse__caisse=caisse, type_mouvement='ENTREE'
            ).aggregate(t=Sum('montant'))['t'] or 0
            sorties = base_qs.filter(
                caisse__caisse=caisse, type_mouvement='SORTIE'
            ).aggregate(t=Sum('montant'))['t'] or 0
            solde_par_caisse.append({
                'nom': caisse.nom,
                'entrees': float(entrees),
                'sorties': float(sorties),
                'solde': float(snap.solde_fermeture) if snap else 0,
            })

        context.update({
            'debut': debut.isoformat(),
            'fin': fin.isoformat(),
            'total_caisses': Caisse.objects.count(),
            'total_entrees': total_entrees,
            'total_sorties': total_sorties,
            'solde_total': total_entrees - total_sorties,
            'mouvements': base_qs.order_by('-date_mouvement')[:300],
            'solde_par_caisse': solde_par_caisse,
            'chart_labels': [c['nom'] for c in solde_par_caisse],
            'chart_entrees': [c['entrees'] for c in solde_par_caisse],
            'chart_sorties': [c['sorties'] for c in solde_par_caisse],
            'chart_soldes': [c['solde'] for c in solde_par_caisse],
        })
        return context


class RapportCommandeView(RoleRequiredMixin, TemplateView):
    allowed_roles = [ROLE_ADMIN]
    template_name = 'rapports/rapport_commande.html'

    def get_context_data(self, **kwargs):
        from produits.models import Stock as StockModel, MouvementStock, Article
        from django.db.models.functions import TruncDate
        from collections import defaultdict

        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        debut_30j = today - datetime.timedelta(days=29)

        # ── 1. Stock actuel (tous magasins) ──────────────────────────
        stock_actuel = {
            row['article_id']: row['qte']
            for row in StockModel.objects.values('article_id').annotate(qte=Sum('qte'))
        }

        # ── 2. Écoulement 30j par article (sorties) ───────────────────
        ecoulement_30j = defaultdict(int)
        for row in (MouvementStock.objects
                    .filter(type=MouvementStock.OUT,
                            date_creation__date__range=(debut_30j, today))
                    .values('article_id')
                    .annotate(total=Sum('qte'))):
            ecoulement_30j[row['article_id']] = row['total']

        # ── 3. Articles à commander (stock actuel ou écoulement > 0) ─
        article_ids = set(stock_actuel.keys()) | set(ecoulement_30j.keys())
        articles = {a.pk: a for a in Article.objects.filter(pk__in=article_ids).select_related('fournisseur', 'unite')}

        # ── 4. Calcul par article ──────────────────────────────────────
        rows = []
        for aid in article_ids:
            a = articles.get(aid)
            if not a:
                continue
            qte_stock = stock_actuel.get(aid, 0)
            ecoul = ecoulement_30j.get(aid, 0)
            ecoul_par_jour = round(ecoul / 30, 2)
            seuil = a.seuil or 0

            if ecoul_par_jour > 0:
                jours_restants = round(qte_stock / ecoul_par_jour, 1)
            else:
                jours_restants = None

            # ── Critères d'inclusion ──────────────────────────────────
            en_rupture  = qte_stock == 0
            sous_seuil  = qte_stock <= seuil
            sous_15j    = jours_restants is not None and jours_restants < 15
            a_commander = en_rupture or sous_seuil or sous_15j

            if not a_commander:
                continue

            # ── Urgence ───────────────────────────────────────────────
            if en_rupture:
                urgence = 'rupture'
            elif sous_seuil or (jours_restants is not None and jours_restants <= 5):
                urgence = 'critique'
            else:
                urgence = 'alerte'

            # ── Quantité suggérée : couvrir 30j nets du stock existant ─
            if ecoul_par_jour > 0:
                qte_suggere = max(0, round(ecoul_par_jour * 30 - qte_stock))
            else:
                # Pas d'écoulement : combler le déficit par rapport au seuil
                qte_suggere = max(0, seuil - qte_stock)

            rows.append({
                'designation'   : a.designation,
                'fournisseur'   : str(a.fournisseur) if a.fournisseur else '—',
                'unite'         : str(a.unite) if a.unite else '—',
                'stock_actuel'  : qte_stock,
                'seuil'         : seuil,
                'ecoul_30j'     : ecoul,
                'ecoul_par_jour': ecoul_par_jour,
                'jours_restants': jours_restants,
                'qte_suggere'   : int(qte_suggere),
                'prix_achat'    : float(a.prix_achat),
                'total_estime'  : round(float(a.prix_achat) * qte_suggere, 0),
                'urgence'       : urgence,
            })

        # Trier : rupture → critique → alerte, puis par jours_restants ↑
        def sort_key(r):
            order = {'rupture': 0, 'critique': 1, 'alerte': 2}
            jr = r['jours_restants'] if r['jours_restants'] is not None else 9999
            return (order[r['urgence']], jr)

        rows.sort(key=sort_key)
        total_estime = sum(r['total_estime'] for r in rows)
        nb_rupture  = sum(1 for r in rows if r['urgence'] == 'rupture')
        nb_critique = sum(1 for r in rows if r['urgence'] == 'critique')
        nb_alerte   = sum(1 for r in rows if r['urgence'] == 'alerte')

        context.update({
            'rows'          : rows,
            'rows_a_commander': rows,
            'total_estime'  : round(total_estime, 0),
            'nb_articles'   : len(rows),
            'nb_rupture'    : nb_rupture,
            'nb_critique'   : nb_critique,
            'nb_alerte'     : nb_alerte,
            'today'         : today.isoformat(),
        })
        return context


# ══════════════════════════════════════════════════════════════════════════════
# Exports PDF
# ══════════════════════════════════════════════════════════════════════════════

def _get_taux():
    """Retourne le taux FC/USD du jour, ou 0 si indisponible."""
    try:
        from parametres.models import get_taux_usd_cdf
        return float(get_taux_usd_cdf())
    except Exception:
        return 0.0


def export_rapport_ventes_pdf(request):
    """Export PDF du rapport des ventes sur la période fournie en GET."""
    today = timezone.now().date()
    try:
        debut = datetime.date.fromisoformat(request.GET.get('debut', ''))
    except ValueError:
        debut = today
    try:
        fin = datetime.date.fromisoformat(request.GET.get('fin', ''))
    except ValueError:
        fin = today

    qs = (Facture.objects
          .filter(date_facture__range=(debut, fin))
          .select_related('cree_par')
          .prefetch_related('facture_client__client'))

    data = []
    for f in qs:
        client = '—'
        if hasattr(f, 'facture_client') and f.facture_client:
            client = str(f.facture_client.client)
        elif f.client_comptoir:
            client = f.client_comptoir
        data.append({
            'numero'      : f.numero,
            'date_facture': f.date_facture.strftime('%d/%m/%Y'),
            'client'      : client,
            'devise'      : f.devise,
            'taux'        : f.taux,
            'remise'      : float(f.remise or 0),
            'total'       : float(f.total or 0),
        })
    data.sort(key=lambda x: x['date_facture'])

    filename = f'RAPPORT_VENTES_{debut.strftime("%Y%m%d")}_{fin.strftime("%Y%m%d")}.pdf'
    title = f'RAPPORT DES VENTES'
    doc = DocumentGenerator(filename, title)
    return doc.generate_rapport_ventes(data, debut=debut, fin=fin, taux=_get_taux())


def export_rapport_resultat_pdf(request):
    """Export PDF du rapport des résultats sur la période fournie en GET."""
    today = timezone.now().date()
    try:
        debut = datetime.date.fromisoformat(request.GET.get('debut', ''))
    except ValueError:
        debut = today.replace(day=1)
    try:
        fin = datetime.date.fromisoformat(request.GET.get('fin', ''))
    except ValueError:
        fin = today

    view = RapportResultatView()
    total_ventes = view._get_resultat_ventes(debut, fin)
    total_appros, _ = view._get_resultat_appros(debut, fin)
    total_global = total_ventes + total_appros
    articles = view._get_resultat_par_article(debut, fin, total_global)

    filename = f'RAPPORT_RESULTATS_{debut.strftime("%Y%m%d")}_{fin.strftime("%Y%m%d")}.pdf'
    doc = DocumentGenerator(filename, 'RAPPORT DES RÉSULTATS')
    return doc.generate_rapport_resultat(
        total_ventes=float(total_ventes),
        total_appros=float(total_appros),
        articles=articles,
        debut=debut,
        fin=fin,
        taux=_get_taux(),
    )


def export_rapport_articles_pdf(request):
    """Export PDF du rapport des articles (stock + CA 30j)."""
    from produits.models import Stock as StockModel, MouvementStock, Article as ArticleModel
    from django.db.models.functions import TruncDate
    from parametres.models import get_taux_usd_cdf
    from collections import defaultdict

    taux = _get_taux()
    today = timezone.now().date()
    debut_30j = today - datetime.timedelta(days=29)

    stock_actuel = {
        row['article_id']: row['qte']
        for row in StockModel.objects.values('article_id').annotate(qte=Sum('qte'))
    }
    aids_ventes = set(
        DetailsFacture.objects
        .filter(facture__date_facture__range=(debut_30j, today))
        .values_list('article_id', flat=True).distinct()
    )
    article_ids = set(stock_actuel.keys()) | aids_ventes
    articles = {a.pk: a for a in ArticleModel.objects.filter(pk__in=article_ids)}

    pv_fc = lambda a: float(a.prix_vente) * taux if a.devise == '$' else float(a.prix_vente)

    valeur_stock = {aid: stock_actuel.get(aid, 0) * pv_fc(articles[aid])
                    for aid in article_ids if aid in articles}
    total_valeur_stock = sum(valeur_stock.values())

    ca_30j = {
        row['article_id']: float(row['ca'] or 0)
        for row in (DetailsFacture.objects
                    .filter(facture__date_facture__range=(debut_30j, today))
                    .values('article_id')
                    .annotate(ca=Sum(F('qte') * F('prix'), output_field=DecimalField())))
    }
    ca_total_30j = sum(ca_30j.values())

    resultat_30j = {
        row['article_id']: float(row['res'] or 0)
        for row in (DetailsFacture.objects
                    .filter(facture__date_facture__range=(debut_30j, today))
                    .values('article_id')
                    .annotate(res=Sum((F('prix') - F('article__prix_achat')) * F('qte'),
                                     output_field=DecimalField())))
    }
    resultat_total_30j = sum(resultat_30j.values())

    rows = []
    for aid in article_ids:
        a = articles.get(aid)
        if not a:
            continue
        val = valeur_stock.get(aid, 0)
        ca  = ca_30j.get(aid, 0)
        res = resultat_30j.get(aid, 0)
        rows.append({
            'designation'  : a.designation,
            'stock_actuel' : stock_actuel.get(aid, 0),
            'valeur_stock' : round(val, 0),
            'pct_stock'    : round(val / total_valeur_stock * 100, 1) if total_valeur_stock else 0,
            'ca_30j'       : round(ca, 0),
            'pct_ca'       : round(ca / ca_total_30j * 100, 1) if ca_total_30j else 0,
            'resultat_30j' : round(res, 0),
            'moy_stock_30j': 0,
        })
    rows.sort(key=lambda x: x['valeur_stock'], reverse=True)

    filename = f'RAPPORT_ARTICLES_{today.strftime("%Y%m%d")}.pdf'
    doc = DocumentGenerator(filename, 'RAPPORT DES ARTICLES')
    return doc.generate_rapport_articles(
        rows=rows,
        total_valeur_stock=round(total_valeur_stock, 0),
        ca_total_30j=round(ca_total_30j, 0),
        resultat_total_30j=round(resultat_total_30j, 0),
        taux=taux,
    )


def export_rapport_caisse_pdf(request):
    """Export PDF du rapport des caisses sur la période fournie en GET."""
    from caisse.models import MouvementCaisse, Caisse
    from patrimoine.models import SnapshotJournalier

    today = timezone.now().date()
    try:
        debut = datetime.date.fromisoformat(request.GET.get('debut', ''))
    except ValueError:
        debut = today
    try:
        fin = datetime.date.fromisoformat(request.GET.get('fin', ''))
    except ValueError:
        fin = today

    base_qs = MouvementCaisse.objects.filter(
        date_mouvement__date__range=(debut, fin)
    ).select_related('caisse', 'caisse__caisse', 'rubrique', 'effectue_par')

    total_entrees = float(base_qs.filter(type_mouvement='ENTREE').aggregate(
        t=Sum('montant'))['t'] or 0)
    total_sorties = float(base_qs.filter(type_mouvement='SORTIE').aggregate(
        t=Sum('montant'))['t'] or 0)

    solde_par_caisse = []
    for caisse in Caisse.objects.all():
        snap = (SnapshotJournalier.objects
                .filter(caisse=caisse, date__lte=fin)
                .order_by('-date').first())
        entrees = float(base_qs.filter(caisse__caisse=caisse, type_mouvement='ENTREE')
                        .aggregate(t=Sum('montant'))['t'] or 0)
        sorties = float(base_qs.filter(caisse__caisse=caisse, type_mouvement='SORTIE')
                        .aggregate(t=Sum('montant'))['t'] or 0)
        solde_par_caisse.append({
            'nom'    : caisse.nom,
            'entrees': entrees,
            'sorties': sorties,
            'solde'  : float(snap.solde_fermeture) if snap else 0,
        })

    mouvements = [
        {
            'date'        : m.date_mouvement.strftime('%d/%m/%Y %H:%M'),
            'caisse'      : str(m.caisse.caisse) if m.caisse else '—',
            'type'        : m.type_mouvement,
            'rubrique'    : str(m.rubrique) if m.rubrique else '—',
            'montant'     : float(m.montant),
            'effectue_par': str(m.effectue_par) if m.effectue_par else '—',
        }
        for m in base_qs.order_by('-date_mouvement')[:300]
    ]

    filename = f'RAPPORT_CAISSES_{debut.strftime("%Y%m%d")}_{fin.strftime("%Y%m%d")}.pdf'
    doc = DocumentGenerator(filename, 'RAPPORT DES CAISSES')
    return doc.generate_rapport_caisse(
        solde_par_caisse=solde_par_caisse,
        mouvements=mouvements,
        total_entrees=total_entrees,
        total_sorties=total_sorties,
        debut=debut,
        fin=fin,
        taux=_get_taux(),
    )


def export_bon_commande_pdf(request):
    """Export PDF du bon de commande (articles à réapprovisionner)."""
    from produits.models import Stock as StockModel, MouvementStock, Article
    from collections import defaultdict

    today = timezone.now().date()
    debut_30j = today - datetime.timedelta(days=29)

    stock_actuel = {
        row['article_id']: row['qte']
        for row in StockModel.objects.values('article_id').annotate(qte=Sum('qte'))
    }
    ecoulement_30j = defaultdict(int)
    for row in (MouvementStock.objects
                .filter(type=MouvementStock.OUT,
                        date_creation__date__range=(debut_30j, today))
                .values('article_id')
                .annotate(total=Sum('qte'))):
        ecoulement_30j[row['article_id']] = row['total']

    article_ids = set(stock_actuel.keys()) | set(ecoulement_30j.keys())
    articles = {
        a.pk: a
        for a in Article.objects.filter(pk__in=article_ids).select_related('fournisseur', 'unite')
    }

    data = []
    for aid in article_ids:
        a = articles.get(aid)
        if not a:
            continue
        qte_stock = stock_actuel.get(aid, 0)
        ecoul = ecoulement_30j.get(aid, 0)
        ecoul_par_jour = round(ecoul / 30, 2)
        seuil = a.seuil or 0

        jours_restants = round(qte_stock / ecoul_par_jour, 1) if ecoul_par_jour > 0 else None

        en_rupture  = qte_stock == 0
        sous_seuil  = qte_stock <= seuil
        sous_15j    = jours_restants is not None and jours_restants < 15

        if not (en_rupture or sous_seuil or sous_15j):
            continue

        if ecoul_par_jour > 0:
            qte_suggere = int(max(0, round(ecoul_par_jour * 30 - qte_stock)))
        else:
            qte_suggere = max(0, seuil - qte_stock)

        if en_rupture:
            urgence = 'rupture'
        elif sous_seuil or (jours_restants is not None and jours_restants <= 5):
            urgence = 'critique'
        else:
            urgence = 'alerte'

        data.append({
            'designation'   : a.designation,
            'fournisseur'   : str(a.fournisseur) if a.fournisseur else '—',
            'unite'         : str(a.unite) if a.unite else '—',
            'stock_actuel'  : qte_stock,
            'seuil'         : seuil,
            'ecoul_par_jour': ecoul_par_jour,
            'jours_restants': jours_restants,
            'qte_suggere'   : qte_suggere,
            'prix_achat'    : float(a.prix_achat),
            'total_estime'  : round(float(a.prix_achat) * qte_suggere, 0),
            'urgence'       : urgence,
        })

    def _sort_key(r):
        order = {'rupture': 0, 'critique': 1, 'alerte': 2}
        jr = r['jours_restants'] if r['jours_restants'] is not None else 9999
        return (order[r['urgence']], jr)

    data.sort(key=_sort_key)

    filename = f'BON_COMMANDE_{today.strftime("%Y%m%d")}.pdf'
    title = f'BON DE COMMANDE — {today.strftime("%d/%m/%Y")}'
    doc = DocumentGenerator(filename, title)
    return doc.generate_bon_commande(data)


# Alias de rétrocompatibilité (ancienne URL export_rapport_pdf/<date_range>/)
def export_rapport_pdf(request, date_range):
    date1, date2 = date_range
    request.GET = request.GET.copy()
    request.GET['debut'] = date1.strftime('%Y-%m-%d')
    request.GET['fin']   = date2.strftime('%Y-%m-%d')
    return export_rapport_ventes_pdf(request)
