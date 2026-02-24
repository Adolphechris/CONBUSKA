from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Subquery, OuterRef, F, Value, Case, When
from django.db.models.functions import Coalesce
from produits.models import Article
from django.db.models import Sum, IntegerField
from produits.models import MouvementStock


class FicheStockView(LoginRequiredMixin, ListView):
    model = Article
    context_object_name = 'articles'
    template_name = 'produits/fiche_stock.html'

    def get_queryset(self):
        # Annoter chaque article avec entrées et sorties
        mouvements_qs = MouvementStock.objects.filter(
            article=OuterRef('pk')).values('article').annotate(
            total_in=Coalesce(Sum(Case(When(type='IN', then=F('qte')), output_field=IntegerField())), 0),
            total_out=Coalesce(Sum(Case(When(type='OUT', then=F('qte')), output_field=IntegerField())), 0),
        ).values('total_in', 'total_out')

        return Article.objects.annotate(
            qte_in=Coalesce(Subquery(mouvements_qs.values('total_in')[:1]), Value(0)),
            qte_out=Coalesce(Subquery(mouvements_qs.values('total_out')[:1]), Value(0)),
            stock_ouverture=Value(0, output_field=IntegerField()),
            stock_final=F('qte_in') - F('qte_out')
        ).order_by('designation')
