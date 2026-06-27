from users.permissions import RoleRequiredMixin, ROLE_ADMIN, ROLE_GERANT_STOCK, ROLE_GERANT_MAGASIN
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404, HttpResponse
from produits.models import Article, Stock
from produits.forms import ArticleCreateForm, ArticleActivateOrDeactivateForm
from approvisionnements.models import DetailsApprovisionnement
from factures.models import DetailsFacture
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import datetime
import decimal


class ArticleView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN, ROLE_GERANT_STOCK, ROLE_GERANT_MAGASIN]
    model = Article
    context_object_name = 'liste_articles'
    template_name = 'produits/article/articles.html'

    def get_queryset(self):
        return Article.objects.all().order_by('designation')


class ArticleDetailsView(RoleRequiredMixin, DetailView):
    allowed_roles = [ROLE_ADMIN, ROLE_GERANT_STOCK, ROLE_GERANT_MAGASIN]
    model = Article
    context_object_name = 'article'
    template_name = 'produits/article/article_details.html'

    def get_mouvement_stock(self):
        """Retourne les entrées et sorties combinées, triées par date décroissante"""
        article = self.object

        mouvements = []

        # Entrées (Approvisionnements)
        entrees_qs = DetailsApprovisionnement.objects.filter(article=article).select_related('approvisionnement')
        for e in entrees_qs:
            mouvements.append({
                'date': e.approvisionnement.date_creation.date(),
                'type': 'ENTREE',
                'qte': e.qte,
                'unite': article.unite.nom,
                'prix': e.prix or article.prix_achat,
                'taux': e.approvisionnement.taux or '-',
                'solde': None,  # calculé plus tard
                'origine': f"Approvisionnement #{e.approvisionnement.numero}",
            })

        # Sorties (Factures)
        sorties_qs = DetailsFacture.objects.filter(article=article).select_related('facture')
        for s in sorties_qs:
            mouvements.append({
                'date': s.facture.date_facture,
                'type': 'SORTIE',
                'qte': -s.qte,  # négatif pour sortie
                'unite': article.unite.nom,
                'prix': s.prix,
                'taux': s.facture.taux or '-',
                'solde': None,  # calculé plus tard
                'origine': f"Facture #{s.facture.numero}",
            })

        # Tri par date décroissante
        mouvements.sort(key=lambda x: x['date'], reverse=True)

        # Calcul du solde courant et consommation moyenne
        solde = 0
        for m in reversed(mouvements):  # solde croissant
            solde += m['qte']
            m['solde'] = solde

        return mouvements

    def consommation_moyenne(self, mouvements):
        article = self.object
        total_sorties = 0
        mois_actifs = set()
        for m in reversed(mouvements):
            if m['type'] == 'SORTIE':
                total_sorties += abs(m['qte'])
                mois_actifs.add(m['date'].month)

        # Consommation moyenne mensuelle
        nb_mois = len(mois_actifs) or 1
        conso_moy = total_sorties / nb_mois

        return f"{round(conso_moy, 2)} {article.unite.nom}/mois"

    def get_stocks(self):
        today = datetime.datetime.today().date()
        stocks = []
        for stock in Stock.objects.filter(article=self.object):
            statut = "Bon"
            if stock.date_peremption:
                delta = (stock.date_peremption - today).days

                if delta < 90:
                    statut = "Urgent"
                elif 90 <= delta < 180:
                    statut = "Surveiller"

            stocks.append({
                'magasin': stock.magasin.nom,
                'qte': stock.qte,
                'date_peremption': stock.date_peremption,
                'statut': statut,
            })

        return stocks

    def rentabilite(self):
        pa = self.object.prix_achat or 0
        pv = self.object.prix_vente or 0

        if pa == 0:
            return None  # ou 0

        return round((pv - pa) / pa * 100, 2)

    def get_fournisseurs_data(self):
        article = self.object
        fournisseurs_map = {}
        details = (DetailsApprovisionnement.objects
                   .filter(article=article)
                   .select_related('fournisseur', 'approvisionnement')
                   .order_by('date_creation'))
        for detail in details:
            fourn = detail.fournisseur
            if not fourn:
                continue
            fid = fourn.pk
            if fid not in fournisseurs_map:
                fournisseurs_map[fid] = {
                    'nom': fourn.nom,
                    'nb_livraisons': 0,
                    'qte_totale': 0,
                    'dernier_prix': 0,
                    'derniere_date': None,
                    'devise': detail.approvisionnement.devise,
                }
            fournisseurs_map[fid]['nb_livraisons'] += 1
            fournisseurs_map[fid]['qte_totale'] += detail.qte
            fournisseurs_map[fid]['dernier_prix'] = detail.prix
            fournisseurs_map[fid]['derniere_date'] = detail.date_creation.date()
            fournisseurs_map[fid]['devise'] = detail.approvisionnement.devise
        return list(fournisseurs_map.values())

    def get_stats(self, mouvements):
        article = self.object
        ca_total = decimal.Decimal(0)
        marge_brute = decimal.Decimal(0)
        nb_sorties = 0
        nb_entrees = 0
        monthly_entrees = defaultdict(int)
        monthly_sorties = defaultdict(int)

        for m in mouvements:
            month_key = m['date'].strftime('%Y-%m')
            if m['type'] == 'SORTIE':
                nb_sorties += 1
                qty = abs(m['qte'])
                prix = decimal.Decimal(str(m['prix'] or 0))
                ca_total += qty * prix
                pa = article.prix_achat or 0
                marge_brute += qty * (prix - pa)
                monthly_sorties[month_key] += qty
            else:
                nb_entrees += 1
                monthly_entrees[month_key] += m['qte']

        all_months = sorted(set(list(monthly_entrees.keys()) + list(monthly_sorties.keys())))
        last_12 = all_months[-12:]

        return {
            'ca_total': round(ca_total, 2),
            'marge_brute': round(marge_brute, 2),
            'nb_sorties': nb_sorties,
            'nb_entrees': nb_entrees,
            'chart_labels': last_12,
            'chart_entrees': [monthly_entrees.get(m, 0) for m in last_12],
            'chart_sorties': [monthly_sorties.get(m, 0) for m in last_12],
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entrees = (DetailsApprovisionnement.objects.filter(article=self.object).
                   aggregate(total=Sum('qte'))['total'] or 0)
        sorties = (DetailsFacture.objects.filter(article=self.object).
                   aggregate(total=Sum('qte'))['total'] or 0)

        mouvements = self.get_mouvement_stock()
        context['article_stocks'] = self.get_stocks()
        context['rentabilite'] = self.rentabilite()
        context['entrees'] = entrees
        context['sorties'] = sorties
        context['mouvements'] = mouvements
        context['consommation_moyenne'] = self.consommation_moyenne(mouvements)
        context['fournisseurs_data'] = self.get_fournisseurs_data()
        context['stats'] = self.get_stats(mouvements)

        # Dual currency: calcul des valeurs USD
        from parametres.models import get_taux_usd_cdf
        from decimal import Decimal
        taux = Decimal(str(get_taux_usd_cdf()))
        context['stock_usd'] = (Decimal(str(self.object.stock)) / taux) if taux else Decimal('0')
        context['entrees_usd'] = (Decimal(str(entrees)) / taux) if taux else Decimal('0')
        context['sorties_usd'] = (Decimal(str(sorties)) / taux) if taux else Decimal('0')

        return context


class ArticleCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [ROLE_ADMIN]
    model = Article
    template_name = 'produits/article/article_create_form.html'
    form_class = ArticleCreateForm


class ArticleUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [ROLE_ADMIN]
    model = Article
    template_name = 'produits/article/article_create_form.html'
    form_class = ArticleCreateForm


class ArticleDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = [ROLE_ADMIN]
    model = Article
    template_name = 'produits/article/article_confirm_delete.html'
    success_url = reverse_lazy('articles')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer un article'
        context['message'] = "Voulez-vous supprimer l'article {} ?".format(self.get_object())
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Valider'
        return context


class ArticleActivateOrDeactivateView(RoleRequiredMixin, FormView):
    allowed_roles = [ROLE_ADMIN]
    form_class = ArticleActivateOrDeactivateForm
    template_name = 'produits/article/activate_deactivate.html'

    def get_article(self):
        return get_object_or_404(Article, pk=self.kwargs["pk"])

    def post(self, request, *args, **kwargs):
        article = self.get_article()
        if article.actif:
            article.actif = False
        else:
            article.actif = True
        article.save(update_fields=['actif'])

        response = HttpResponse()
        response["HX-Redirect"] = reverse('articles')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.get_article()
        title = 'Désactiver' if article.actif else 'Activer'


        context['title'] = f'{title} article'
        context['message'] = f"Êtes-vous sûr de vouloir {title.lower()} l'article #{article.designation} ?"
        context['submit_icon'] = 'fa fa-check'
        context['submit_label'] = 'Oui'
        context['article'] = article
        return context
