import logging

from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import TemplateView, RedirectView, View, ListView
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from users.permissions import RoleRequiredMixin, ALL_ROLES
import json
from operator import itemgetter
from itertools import groupby
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
from clients.models import Client
from fournisseurs.models import Fournisseur
from creanciers.models import Creancier, Debiteur
from factures.models import Facture, DetailsFacture
from parametres.models import Magasin
from produits.models import Article, Stock, MouvementStock
from commandes.models import Commande
from caisse.selectors import get_total_ventes_caisse
from django.db.models import Sum, F, DecimalField, Value, Prefetch, Case, When, IntegerField, Q, Max
from django.db.models.functions import ExtractMonth, Coalesce
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta


class DashboardAdminView(RoleRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    allowed_roles = ALL_ROLES

    @staticmethod
    def calculate_ca(day):
        qs = (Facture.objects
              .filter(date_facture=day)
              .annotate(
                    total_lignes=Sum(F('facture_details__qte') * F('facture_details__prix'),
                    output_field = DecimalField(max_digits=18, decimal_places=2))
              )
              .annotate(
                    total_vendu=F('total_lignes') - F('remise')
              )
              .aggregate(total=Coalesce(Sum('total_vendu'), Value(0),
                                        output_field=DecimalField(max_digits=18, decimal_places=2)))
        )
        return qs['total']

    def get_ca(self):
        """ Calcul du chiffre d'affaire du jour en cours + comparaison avec le CA de la veille """
        today = timezone.localtime(timezone.now()).date()
        yesterday = today - timedelta(days=1)

        ca_today = self.calculate_ca(today)
        ca_yesterday = self.calculate_ca(yesterday)
        difference = ca_today - ca_yesterday

        logger.debug("CA today=%s yesterday=%s diff=%s", ca_today, ca_yesterday, difference)

        if ca_yesterday == 0:
            stat = Decimal('100') if ca_today > 0 else Decimal('0')
        else:
            stat = (difference * Decimal('100')) / ca_yesterday
        return ca_today, stat

    @staticmethod
    def get_mois():
        mois_labels = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre',
                       'Novembre', 'Décembre']
        return mois_labels

    @staticmethod
    def ventes_par_mois():
        current_year = datetime.now().year

        qs = (Facture.objects
              .filter(date_facture__year=current_year)
              .annotate(mois=ExtractMonth('date_facture'))
              .values('mois')
              .annotate(
                    total_lignes=Sum(
                        F('facture_details__qte') * F('facture_details__prix'),
                        output_field=DecimalField(max_digits=18, decimal_places=2)
                    ) - Sum(F('remise'))
              )
              .order_by('mois')
        )
        return qs

    def get_ventes_chart(self):
        data = [0] * 12  # initialise 12 mois à zéro
        qs = self.ventes_par_mois()

        for item in qs:
            mois = item['mois']
            total = item['total_lignes'] or 0
            data[mois - 1] = float(total)  # -1 car liste commence à 0

        return data

    @staticmethod
    def top_articles():
        articles_ca = (
            DetailsFacture.objects
            .annotate(
                ca=F('qte') * F('prix')
            )
            .values('article__designation', 'article__id')
            .annotate(
                total_qte=Sum('qte'),
                total_ca=Sum('ca', output_field=DecimalField(max_digits=18, decimal_places=2))
            )
            .order_by('-total_ca')  # Classement du plus grand au plus petit
        )
        return articles_ca

    @staticmethod
    def articles_expiration():
        today = datetime.today()
        limit_date = today + relativedelta(months=3)

        return (
            Stock.objects
                .filter(date_peremption__range=(today, limit_date))
                .select_related('article', 'magasin')
                .order_by('date_peremption')
        )

    @staticmethod
    def articles_critiques():
        magasin = Magasin.objects.filter(is_principal=True).first()
        if not magasin:
            return 0

        return (
            Article.objects
            .annotate(
                stock_actuel=Coalesce(
                    Sum(
                        Case(
                            When(
                                mouvementstock__type=MouvementStock.IN,
                                then=F("mouvementstock__qte")
                            ),
                            When(
                                mouvementstock__type=MouvementStock.OUT,
                                then=-F("mouvementstock__qte")
                            ),
                            filter=Q(mouvementstock__magasin=magasin),
                            output_field=IntegerField(),
                        )
                    ),
                    0
                )
            )
            .filter(stock_actuel__lt=F("seuil"))
            .count()
        )

    # ── Nouveaux calculs ───────────────────────────────────────────────────

    @staticmethod
    def get_solde_caisses():
        """Retourne (total_solde, liste de dicts par caisse ouverte) avec conversion USD."""
        from caisse.models import CaisseCourante
        from parametres.models import get_taux_usd_cdf
        from decimal import Decimal
        
        caisses = CaisseCourante.objects.filter(est_ouverte=True).select_related('caisse')
        result = []
        total = Decimal('0')
        
        taux = Decimal(str(get_taux_usd_cdf()))
        
        for cc in caisses:
            ventes = get_total_ventes_caisse(caisse_courante=cc)
            entrees = cc.mouvements.filter(type_mouvement='ENTREE').aggregate(
                t=Coalesce(Sum('montant'), Value(0),
                           output_field=DecimalField(max_digits=14, decimal_places=2))
            )['t']
            sorties = cc.mouvements.filter(type_mouvement='SORTIE').aggregate(
                t=Coalesce(Sum('montant'), Value(0),
                           output_field=DecimalField(max_digits=14, decimal_places=2))
            )['t']
            solde = cc.solde_initial + ventes + entrees - sorties
            total += solde
            
            # Conversion USD
            solde_usd = (solde / taux) if taux else Decimal('0')
            ventes_usd = (ventes / taux) if taux else Decimal('0')
            entrees_usd = (entrees / taux) if taux else Decimal('0')
            sorties_usd = (sorties / taux) if taux else Decimal('0')
            
            result.append({
                'cc': cc,
                'nom': cc.caisse.nom,
                'solde_initial': cc.solde_initial,
                'ventes': ventes,
                'ventes_usd': ventes_usd,
                'entrees': entrees,
                'entrees_usd': entrees_usd,
                'sorties': sorties,
                'sorties_usd': sorties_usd,
                'solde': solde,
                'solde_usd': solde_usd,
            })
        
        total_usd = (total / taux) if taux else Decimal('0')
        return total, total_usd, result

    @staticmethod
    def get_creances_dettes():
        """Retourne (total_creances, total_dettes) en USD.
        
        Note: solde() retourne solde_usd() par défaut depuis la migration bi-devise.
        Les valeurs retournées sont donc en USD.
        """
        total_c = sum(c.solde() for c in Creancier.objects.all())
        total_d = sum(d.solde() for d in Debiteur.objects.all())
        return Decimal(str(total_c or 0)), Decimal(str(total_d or 0))

    @staticmethod
    def get_paie_mois():
        """Total des montants perçus sur les fiches de paie du mois courant."""
        from paie.models import Paie
        now = timezone.now()
        return Paie.objects.filter(
            mois__year=now.year, mois__month=now.month
        ).aggregate(
            total=Coalesce(Sum('net_a_payer'), Value(0),
                           output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total']

    @staticmethod
    def get_categories_chart():
        """Labels + données pour le donut répartition des ventes par catégorie (année en cours)."""
        current_year = datetime.now().year
        qs = list(
            DetailsFacture.objects
            .filter(facture__date_facture__year=current_year)
            .values('article__categorie__nom')
            .annotate(total=Sum(
                F('qte') * F('prix'),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ))
            .order_by('-total')[:7]
        )
        labels = [item['article__categorie__nom'] or 'Sans catégorie' for item in qs]
        data = [float(item['total'] or 0) for item in qs]
        return labels, data

    @staticmethod
    def get_depenses_chart():
        """12 totaux mensuels de dépenses caisse (SORTIE) pour l'année en cours."""
        from caisse.models import MouvementCaisse
        current_year = datetime.now().year
        qs = (
            MouvementCaisse.objects
            .filter(date_mouvement__year=current_year, type_mouvement='SORTIE')
            .annotate(mois=ExtractMonth('date_mouvement'))
            .values('mois')
            .annotate(total=Coalesce(Sum('montant'), Value(0),
                                     output_field=DecimalField(max_digits=14, decimal_places=2)))
            .order_by('mois')
        )
        data = [0] * 12
        for item in qs:
            data[item['mois'] - 1] = float(item['total'] or 0)
        return data

    @staticmethod
    def get_stat_variation(count_this: int, count_last: int) -> float:
        if count_last == 0:
            return 100.0 if count_this > 0 else 0.0
        return round((count_this - count_last) / count_last * 100, 1)

    # ── Context ────────────────────────────────────────────────────────────

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        now = timezone.localtime(timezone.now())
        today = now.date()
        current_year = now.year
        current_month = now.month
        first_this_month = today.replace(day=1)
        last_month_date = first_this_month - timedelta(days=1)

        from parametres.models import get_taux_usd_cdf
        current_taux = Decimal(str(get_taux_usd_cdf(today)))

        # ── KPI Ligne 1 : financier ───────────────────────────────────────
        solde_caisses_total, solde_caisses_total_usd, caisses_detail = self.get_solde_caisses()
        context_data['solde_caisses_total'] = solde_caisses_total
        context_data['solde_caisses_total_usd'] = solde_caisses_total_usd
        context_data['caisses_detail'] = caisses_detail

        ca, stat_ca = self.get_ca()
        context_data['ca'] = ca
        context_data['ca_usd'] = (ca / current_taux) if current_taux else Decimal('0')
        context_data['stat_ca'] = round(stat_ca, 2)

        context_data['factures_jour_count'] = Facture.objects.filter(date_facture=today).count()

        total_creances, total_dettes = self.get_creances_dettes()
        # get_creances_dettes() retourne déjà des valeurs en USD
        context_data['total_creances'] = total_creances  # USD
        context_data['total_creances_usd'] = total_creances  # USD (déjà en USD)
        context_data['total_dettes'] = total_dettes  # USD
        context_data['total_dettes_usd'] = total_dettes  # USD (déjà en USD)

        # ── KPI Ligne 2 : opérationnel ────────────────────────────────────
        context_data['articles'] = self.articles_critiques()

        commandes_ce_mois = Commande.objects.filter(
            date_creation__year=current_year,
            date_creation__month=current_month,
        ).count()
        commandes_mois_dernier = Commande.objects.filter(
            date_creation__year=last_month_date.year,
            date_creation__month=last_month_date.month,
        ).count()
        context_data['commandes'] = Commande.objects.count()
        context_data['commandes_ce_mois'] = commandes_ce_mois
        context_data['stat_commandes'] = self.get_stat_variation(
            commandes_ce_mois, commandes_mois_dernier
        )

        factures_nv_qs = Facture.objects.filter(
            valide=False, actif=True
        ).prefetch_related('facture_client__client')
        context_data['factures_non_validees_count'] = factures_nv_qs.count()
        context_data['factures_non_validees'] = factures_nv_qs.order_by('-date_facture')[:5]

        context_data['paie_mois'] = self.get_paie_mois()

        # Taux de change actuel
        from parametres.models import get_taux_usd_cdf, TauxEchange
        try:
            taux_actuel = get_taux_usd_cdf()
            taux_obj = TauxEchange.objects.filter(
                devise_source='USD',
                devise_cible='CDF'
            ).order_by('-effective_date').first()
            context_data['taux_courant'] = taux_actuel
            context_data['taux_date'] = taux_obj.effective_date if taux_obj else None
            context_data['taux_usd'] = Decimal(str(taux_actuel))
        except Exception:
            context_data['taux_courant'] = None
            context_data['taux_date'] = None
            context_data['taux_usd'] = Decimal('0')

        # Comptages historiques (compatibilité)
        context_data['clients'] = Client.objects.count()
        context_data['fournisseurs'] = Fournisseur.objects.count()
        context_data['creanciers'] = Creancier.objects.count()
        context_data['debiteurs'] = Debiteur.objects.count()
        context_data['factures'] = Facture.objects.count()

        # ── Graphiques ────────────────────────────────────────────────────
        context_data['current_year'] = current_year
        context_data['mois_labels'] = self.get_mois()
        context_data['chart_data'] = self.get_ventes_chart()
        context_data['depenses_chart_data'] = self.get_depenses_chart()

        categories_labels, categories_data = self.get_categories_chart()
        context_data['categories_labels'] = categories_labels
        context_data['categories_data'] = categories_data

        # ── Top articles + progress bars dynamiques ───────────────────────
        articles_ca = self.top_articles()[:10]
        context_data['top_articles'] = articles_ca
        first_article = articles_ca[0] if articles_ca else None
        context_data['top_articles_max'] = (
            first_article['total_ca'] if first_article else Decimal('1')
        )

        # ── Panels opérationnels ──────────────────────────────────────────
        context_data['commandes_recentes'] = (
            Commande.objects.select_related('fournisseur').order_by('-date_creation')[:5]
        )
        context_data['articles_expiration'] = self.articles_expiration()

        # ── Journal d'activités ───────────────────────────────────────────
        from activity_logs.models import ActivityLog
        context_data['recent_logs'] = ActivityLog.objects.select_related('user').all()[:10]

        return context_data



class DashboardBaseView(RoleRequiredMixin, View):
    login_url = '/login/'
    allowed_roles = ALL_ROLES
    admin_view = staticmethod(DashboardAdminView.as_view())

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        else:
            if str(self.request.user.username) != 'DOE':
                return self.admin_view(request, *args, **kwargs)

            else:
                pass


class TopArticlesView(RoleRequiredMixin, TemplateView):
    template_name = 'dashboard/top_articles.html'
    allowed_roles = ALL_ROLES
    PER_PAGE = 25

    TRI_CHOICES = {
        'ca': ('-total_ca', 'Chiffre d\'affaires'),
        'qte': ('-total_qte', 'Volume de vente'),
        'moins': ('total_ca', 'Moins vendus (CA)'),
        'moins_qte': ('total_qte', 'Moins vendus (volume)'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tri = self.request.GET.get('tri', 'ca')
        if tri not in self.TRI_CHOICES:
            tri = 'ca'

        order_field, tri_label = self.TRI_CHOICES[tri]

        qs = (
            DetailsFacture.objects
            .annotate(ca=F('qte') * F('prix'))
            .values('article__designation', 'article__id')
            .annotate(
                total_qte=Sum('qte'),
                total_ca=Sum('ca', output_field=DecimalField(max_digits=18, decimal_places=2))
            )
            .order_by(order_field)
        )

        total_count = qs.count()
        max_vals = qs.aggregate(max_ca=Max('total_ca'), max_qte=Max('total_qte'))
        max_ca = max_vals['max_ca'] or Decimal('1')
        max_qte = max_vals['max_qte'] or 1

        paginator = Paginator(qs, self.PER_PAGE)
        page_num = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_num)

        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['total'] = total_count
        context['tri'] = tri
        context['tri_label'] = tri_label
        context['tri_choices'] = self.TRI_CHOICES
        context['max_ca'] = max_ca or Decimal('1')
        context['max_qte'] = max_qte or 1
        return context
