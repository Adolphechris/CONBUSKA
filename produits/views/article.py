from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from produits.models import Article, Stock
from produits.forms import ArticleCreateForm
from approvisionnements.models import DetailsApprovisionnement
from factures.models import DetailsFacture
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
import datetime


class ArticleView(LoginRequiredMixin, ListView):
    model = Article
    context_object_name = 'liste_articles'
    template_name = 'produits/article/articles.html'


class ArticleDetailsView(LoginRequiredMixin, DetailView):
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
        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    template_name = 'produits/article/article_create_form.html'
    form_class = ArticleCreateForm


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = Article
    template_name = 'produits/article/article_create_form.html'
    form_class = ArticleCreateForm


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
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