from datetime import date

from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from users.permissions import RoleRequiredMixin, ROLE_ADMIN, ROLE_GERANT_STOCK, ROLE_GERANT_MAGASIN
from django.db.models import Subquery, OuterRef, F, Value, Case, When, Sum, IntegerField
from django.db.models.functions import Coalesce
from parametres.models import Magasin
from produits.models import Article, MouvementStock


class FicheStockView(RoleRequiredMixin, ListView):
    allowed_roles = [ROLE_ADMIN, ROLE_GERANT_STOCK, ROLE_GERANT_MAGASIN]
    model = Article
    context_object_name = 'articles'
    template_name = 'produits/fiche_stock.html'

    def get_magasin(self):
        """Magasin cible : paramètre GET, magasin principal, ou premier magasin par défaut."""
        magasin_id = self.request.GET.get('magasin')
        if magasin_id:
            return get_object_or_404(Magasin, pk=magasin_id)
        return (
            Magasin.objects.filter(is_principal=True).first()
            or Magasin.objects.order_by('pk').first()
        )

    def get_periode(self):
        """Période : paramètres GET debut/fin (YYYY-MM-DD), défaut = aujourd'hui."""
        today = date.today()
        try:
            debut = date.fromisoformat(self.request.GET.get('debut', ''))
        except ValueError:
            debut = today
        try:
            fin = date.fromisoformat(self.request.GET.get('fin', ''))
        except ValueError:
            fin = today

        if debut > fin:
            debut, fin = fin, debut
        return debut, fin

    def get_queryset(self):
        magasin = self.get_magasin()
        if not magasin:
            return Article.objects.none()

        debut, fin = self.get_periode()

        # Stock ouverture : IN - OUT AVANT la période (stock de clôture de la veille)
        sq_open_in = (
            MouvementStock.objects
            .filter(article=OuterRef('pk'), magasin=magasin, type='IN', date_creation__date__lt=debut)
            .values('article').annotate(total=Sum('qte')).values('total')
        )
        sq_open_out = (
            MouvementStock.objects
            .filter(article=OuterRef('pk'), magasin=magasin, type='OUT', date_creation__date__lt=debut)
            .values('article').annotate(total=Sum('qte')).values('total')
        )

        # Mouvements de la période [debut, fin]
        sq_period_in = (
            MouvementStock.objects
            .filter(article=OuterRef('pk'), magasin=magasin, type='IN',
                    date_creation__date__range=(debut, fin))
            .values('article').annotate(total=Sum('qte')).values('total')
        )
        sq_period_out = (
            MouvementStock.objects
            .filter(article=OuterRef('pk'), magasin=magasin, type='OUT',
                    date_creation__date__range=(debut, fin))
            .values('article').annotate(total=Sum('qte')).values('total')
        )

        return Article.objects.annotate(
            _open_in=Coalesce(Subquery(sq_open_in), Value(0), output_field=IntegerField()),
            _open_out=Coalesce(Subquery(sq_open_out), Value(0), output_field=IntegerField()),
            stock_ouverture=F('_open_in') - F('_open_out'),
            qte_in=Coalesce(Subquery(sq_period_in), Value(0), output_field=IntegerField()),
            qte_out=Coalesce(Subquery(sq_period_out), Value(0), output_field=IntegerField()),
            stock_final=F('_open_in') - F('_open_out') + Coalesce(Subquery(sq_period_in), Value(0), output_field=IntegerField()) - Coalesce(Subquery(sq_period_out), Value(0), output_field=IntegerField()),
        ).order_by('designation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        magasin = self.get_magasin()
        debut, fin = self.get_periode()

        # Totaux de la période pour les stat cards
        totaux = MouvementStock.objects.filter(
            magasin=magasin,
            date_creation__date__range=(debut, fin),
        ).aggregate(
            total_in=Coalesce(
                Sum(Case(When(type='IN', then=F('qte')), output_field=IntegerField())),
                Value(0)
            ),
            total_out=Coalesce(
                Sum(Case(When(type='OUT', then=F('qte')), output_field=IntegerField())),
                Value(0)
            ),
        )

        context['magasin_courant'] = magasin
        context['magasins'] = Magasin.objects.all().order_by('nom')
        context['debut'] = debut.strftime('%Y-%m-%d')
        context['fin'] = fin.strftime('%Y-%m-%d')
        context['debut_display'] = debut.strftime('%d/%m/%Y')
        context['fin_display'] = fin.strftime('%d/%m/%Y')
        context['total_in'] = totaux['total_in']
        context['total_out'] = totaux['total_out']
        context['stock_net'] = totaux['total_in'] - totaux['total_out']
        return context
