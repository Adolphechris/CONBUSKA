from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.views.generic import ListView, DetailView, TemplateView, RedirectView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import redirect, get_object_or_404, render, HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.urls import reverse_lazy, reverse
from django.template.loader import render_to_string
from django.db.models import Min
import random
from factures.models import Facture, DetailsFacture
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import ExtractMonth
from django.utils import timezone
import datetime
from utils.pdf_generator import DocumentGenerator
from parametres.models import Parametre
from operator import itemgetter


class RapportVenteView(LoginRequiredMixin, TemplateView):
    template_name = 'rapports/rapport_vente.html'

    def get_factures(self):
        # first_date = datetime.datetime.today().replace(day=1).date()
        factures_qs = Facture.objects.filter(date_facture__gte=datetime.datetime.today().date())
        return factures_qs

    def get_ca(self):
        ca = sum(facture.total for facture in self.get_factures())
        return ca

    def get_mois(self):
        mois_labels = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre',
                       'Novembre', 'Décembre']
        return mois_labels

    @staticmethod
    def ventes_par_mois():
        current_year = timezone.now().year

        qs = (Facture.objects
                .filter(date_facture__year=current_year)
                .annotate(mois=ExtractMonth('date_facture'))
                .values('mois')
                .annotate(
                    total_vendu=Sum(
                        F('facture_details__qte') * F('facture_details__prix'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ) - Sum('remise')
                )
                .order_by('mois')
        )
        return qs

    def get_ventes_chart(self):
        data = [0] * 12  # initialise 12 mois à zéro
        qs = self.ventes_par_mois()

        for item in qs:
            mois = item['mois']
            total = item['total_vendu'] or 0
            data[mois - 1] = float(total)  # -1 car liste commence à 0

        return data


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ventes = Facture.objects.ventes_journalieres()
        for i in ventes:
            print('Vente :', i)

        context['total_ventes'] = self.get_ca()
        context['ventes'] = Facture.objects.ventes_journalieres()
        context['mois_labels'] = self.get_mois()
        context['chart_data'] = self.get_ventes_chart()
        return context


class RapportVenteDetailsView(LoginRequiredMixin, TemplateView):
    template_name = 'rapports/rapport_vente_details.html'

    def get_factures(self):
        factures_qs = Facture.objects.filter(date_facture=self.kwargs['date_facture'])
        return factures_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['factures'] = self.get_factures()
        return context


class RapportVenteDetailsFactureView(LoginRequiredMixin, DetailView):
    model = Facture
    template_name = 'rapports/rapport_vente_details_facture.html'

    def get_details_facture(self):
        details_facture = DetailsFacture.objects.filter(facture=self.kwargs['pk'])
        return details_facture

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['details_facture'] = self.get_details_facture()
        return context


class RapportResultatView(LoginRequiredMixin, TemplateView):
    template_name = 'rapports/rapport_resultat.html'

    def get_resultat_ventes(self):
        today = timezone.now().date()
        premier_jour = today.replace(day=1)
        return (DetailsFacture.objects
                .filter(facture__date_facture__range=(premier_jour, today))
                .annotate(resultat=(F('prix') - F('article__prix_achat')) * F('qte'))
                .aggregate(total=Sum('resultat', output_field=DecimalField()))['total'] or 0
        )

    def get_resultat_ventes_par_article(self):
        today = timezone.now().date()
        premier_jour = today.replace(day=1)

        qs = (DetailsFacture.objects
              .filter(facture__date_facture__range=(premier_jour, today))
              .values('article__id', 'article__designation')
              .annotate(
                    resultat=Sum((F('prix') - F('article__prix_achat')) * F('qte'),
                                 output_field=DecimalField(max_digits=12, decimal_places=2)
                                )
                    )
              .order_by('-resultat')
        )

        # Calcul du total global
        total_global = self.get_resultat_ventes() # sum(item['resultat'] for item in qs if item['resultat'])

        # Ajout du pourcentage pour chaque article
        results = []
        for item in qs:
            pourcentage = (item['resultat'] / total_global * 100) if total_global > 0 else 0
            results.append({
                'article_id': item['article__id'],
                'designation': item['article__designation'],
                'resultat': item['resultat'],
                'pourcentage': round(pourcentage, 2)
            })

        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_ventes'] = self.get_resultat_ventes()
        context['resultat_articles'] = self.get_resultat_ventes_par_article()
        return context


class RapportArticleView(LoginRequiredMixin, TemplateView):
    template_name = 'rapports/rapport_article.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_ventes'] = 5000
        return context


class RapportCaisseView(LoginRequiredMixin, TemplateView):
    template_name = 'rapports/rapport_caisse.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_caisses'] = 3
        context['total_entrees'] = 700000
        context['total_sorties'] = 200000
        context['solde_total'] = 500000
        return context


def export_rapport_pdf(request, date_range):
    date1, date2 = date_range
    filename = 'RAPPORT VENTES {}-{}.pdf'.format(date1.strftime("%Y-%m-%d"), date2.strftime("%Y-%m-%d"))
    title = 'RAPPORT DES VENTES du {} au {}'.format(date1.strftime("%Y-%m-%d"), date2.strftime("%Y-%m-%d"))
    doc = DocumentGenerator(filename, title)

    get_params = Parametre.objects.get(code='Params')

    current_year = timezone.now().year
    qs = Facture.objects.all()
    data = []

    for i in qs:
        dico = dict()
        dico['numero'] = i.numero
        dico['date_facture'] = i.date_facture.strftime('%d-%m-%Y')
        dico['devise'] = i.devise
        dico['taux'] = i.taux
        dico['remise'] = i.remise
        dico['client'] = i.client_comptoir
        dico['livreur'] = i.livreur
        dico['total'] = i.total
        dico['cree_par'] = i.cree_par
        data.append(dico)

    data.sort(key=itemgetter('date_facture'))
    return doc.generate_rapport(data)
