from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView, RedirectView, View
from django.urls import reverse_lazy
import json
from operator import itemgetter
from itertools import groupby
from datetime import datetime, timedelta
from clients.models import Client
from fournisseurs.models import Fournisseur
from creanciers.models import Creancier, Debiteur
from factures.models import Facture, DetailsFacture
from parametres.models import Magasin
from produits.models import Article, Stock, MouvementStock
from commandes.models import Commande
from django.db.models import Sum, F, DecimalField, Value, Prefetch, Case, When, IntegerField, Q
from django.db.models.functions import ExtractMonth, Coalesce
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta


class DashboardAdminView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

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

        print(ca_today, ca_yesterday, difference)

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
            print('### ', item)
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

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['clients'] = Client.objects.count()
        context_data['fournisseurs'] = Fournisseur.objects.count()
        context_data['creanciers'] = Creancier.objects.count()
        context_data['debiteurs'] = Debiteur.objects.count()
        context_data['factures'] = Facture.objects.count()
        context_data['articles'] = self.articles_critiques()
        context_data['commandes'] = Commande.objects.count()
        context_data['current_year'] = datetime.now().year

        context_data['mois_labels'] = self.get_mois()
        context_data['chart_data'] = self.get_ventes_chart()

        ca, stat_ca = self.get_ca()
        context_data['ca'] = ca
        context_data['stat_ca'] = round(stat_ca, 2)

        context_data['top_articles'] = self.top_articles()
        context_data['articles_expiration'] = self.articles_expiration()

        return context_data



class DashboardBaseView(LoginRequiredMixin, View):
    login_url = '/login/'
    admin_view = staticmethod(DashboardAdminView.as_view())

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        else:
            if str(self.request.user.username) != 'DOE':
                return self.admin_view(request, *args, **kwargs)

            else:
                pass
