from django.shortcuts import get_object_or_404
from django.views.generic import ListView
from users.permissions import RoleRequiredMixin, ROLE_ADMIN, ROLE_GERANT_STOCK, ROLE_GERANT_MAGASIN
from django.db.models import Subquery, OuterRef, F, Value, Case, When
from django.db.models.functions import Coalesce
from parametres.models import Magasin
from produits.models import Article
from django.db.models import Sum, IntegerField
from produits.models import MouvementStock


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

    def get_queryset(self):
        magasin = self.get_magasin()
        if not magasin:
            return Article.objects.none()

        # Annoter chaque article avec entrées et sorties pour CE MAGASIN uniquement.
        # Évite la confusion : un transfert A→B ne double plus les entrées (IN en B
        # et OUT en A sont ventilés correctement par magasin).
        mouvements_qs = MouvementStock.objects.filter(
            article=OuterRef('pk'),
            magasin=magasin,
        ).values('article').annotate(
            total_in=Coalesce(Sum(Case(When(type='IN', then=F('qte')), output_field=IntegerField())), 0),
            total_out=Coalesce(Sum(Case(When(type='OUT', then=F('qte')), output_field=IntegerField())), 0),
        ).values('total_in', 'total_out')

        return Article.objects.annotate(
            qte_in=Coalesce(Subquery(mouvements_qs.values('total_in')[:1]), Value(0)),
            qte_out=Coalesce(Subquery(mouvements_qs.values('total_out')[:1]), Value(0)),
            stock_ouverture=Value(0, output_field=IntegerField()),
            stock_final=F('qte_in') - F('qte_out')
        ).order_by('designation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['magasin_courant'] = self.get_magasin()
        context['magasins'] = Magasin.objects.all().order_by('nom')
        return context
