from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import FormView

from produits.models import Article
from users.permissions import RoleRequiredMixin, ROLE_ADMIN

from .models import EcommerceLog, ImageArticle, SyncQueue


class EcommerceDashboardView(RoleRequiredMixin, ListView):
    """Vue d'ensemble de la boutique en ligne : stats, articles publiés, logs."""
    allowed_roles = [ROLE_ADMIN]
    model = Article
    template_name = 'ecommerce/dashboard.html'
    context_object_name = 'articles_publies'

    def get_queryset(self):
        return Article.objects.filter(
            est_publie=True
        ).select_related('categorie').order_by('-date_modification')[:50]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        total_articles = Article.objects.count()
        publies = Article.objects.filter(est_publie=True).count()
        non_publies = Article.objects.filter(est_publie=False).count()

        ctx.update({
            'total_articles': total_articles,
            'publies': publies,
            'non_publies': non_publies,
            'sync_en_attente': SyncQueue.objects.filter(statut='pending').count(),
            'sync_echouees': SyncQueue.objects.filter(statut='failed').count(),
            'total_images': ImageArticle.objects.count(),
            'recent_logs': EcommerceLog.objects.select_related(
                'article'
            ).order_by('-timestamp')[:20] if EcommerceLog.objects.exists() else [],
        })
        return ctx


class ArticleEcommerceListView(RoleRequiredMixin, ListView):
    """Liste des articles avec filtre publié/non publié."""
    allowed_roles = [ROLE_ADMIN]
    model = Article
    template_name = 'ecommerce/articles_list.html'
    context_object_name = 'articles'
    paginate_by = 50

    def get_queryset(self):
        qs = Article.objects.select_related('categorie')
        filtre = self.request.GET.get('filtre', 'tous')
        recherche = self.request.GET.get('q', '')

        if filtre == 'publies':
            qs = qs.filter(est_publie=True)
        elif filtre == 'non_publies':
            qs = qs.filter(est_publie=False)

        if recherche:
            qs = qs.filter(
                Q(designation__icontains=recherche)
                | Q(code__icontains=recherche)
            )
        return qs.order_by('-date_modification')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtre'] = self.request.GET.get('filtre', 'tous')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class TogglePublicationView(RoleRequiredMixin, View):
    """Publier ou dépublier un article (toggle)."""
    allowed_roles = [ROLE_ADMIN]

    def post(self, request, pk):
        article = Article.objects.get(pk=pk)
        article.est_publie = not article.est_publie
        article.save(update_fields=['est_publie'])
        etat = 'publié' if article.est_publie else 'dépublié'
        messages.success(request, f"Article {article.designation} {etat} avec succès.")
        return redirect(request.GET.get('next', reverse_lazy('ecommerce_articles')))


class SyncLogsView(RoleRequiredMixin, ListView):
    """Journal des opérations de synchronisation."""
    allowed_roles = [ROLE_ADMIN]
    model = EcommerceLog
    template_name = 'ecommerce/sync_logs.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        qs = EcommerceLog.objects.all()
        filtre = self.request.GET.get('filtre', 'tous')
        if filtre == 'erreurs':
            qs = qs.filter(success=False)
        elif filtre == 'success':
            qs = qs.filter(success=True)
        return qs.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtre'] = self.request.GET.get('filtre', 'tous')
        return ctx


class SyncQueueView(RoleRequiredMixin, ListView):
    """File d'attente des synchronisations."""
    allowed_roles = [ROLE_ADMIN]
    model = SyncQueue
    template_name = 'ecommerce/sync_queue.html'
    context_object_name = 'queue'
    paginate_by = 50

    def get_queryset(self):
        qs = SyncQueue.objects.select_related('article')
        filtre = self.request.GET.get('filtre', 'tous')
        if filtre == 'pending':
            qs = qs.filter(statut='pending')
        elif filtre == 'failed':
            qs = qs.filter(statut='failed')
        elif filtre == 'completed':
            qs = qs.filter(statut='completed')
        return qs.order_by('-date_creation')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtre'] = self.request.GET.get('filtre', 'tous')
        return ctx


class ForceSyncView(RoleRequiredMixin, View):
    """Forcer la synchronisation de tous les articles."""
    allowed_roles = [ROLE_ADMIN]

    def post(self, request):
        from ecommerce.sync.services import FirestoreSyncService

        success, errors = FirestoreSyncService.sync_all(force=True)
        messages.success(
            request,
            f"Synchronisation forcée : {success} succès, {errors} échecs."
        )
        return redirect(reverse_lazy('ecommerce_dashboard'))


def sync_dashboard_view(request):
    """Vue du dashboard de synchronisation Firestore pour l'admin."""
    from django.contrib import admin
    from django.utils import timezone
    from ecommerce.sync.services import FirestoreSyncService
    from produits.models import Article
    
    # Vérifier les permissions admin
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Accès refusé")
    
    # Récupérer les statistiques
    stats = FirestoreSyncService.get_sync_stats()
    
    # Récupérer les articles récemment synchronisés
    recent_syncs = Article.objects.filter(
        derniere_sync_firestore__isnull=False
    ).order_by('-derniere_sync_firestore')[:10]
    
    # Compter les articles
    total_articles = Article.objects.count()
    published_articles = Article.objects.filter(est_publie=True).count()
    unpublished_articles = Article.objects.filter(est_publie=False).count()
    
    # Gérer la requête AJAX pour sync manuelle
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        import json
        data = json.loads(request.body)
        if data.get('action') == 'sync':
            try:
                success, errors = FirestoreSyncService.sync_all(force=True)
                return JsonResponse({
                    'success': True,
                    'message': f'{success} articles synchronisés, {errors} erreurs'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
    
    context = {
        'title': 'Dashboard Synchronisation Firestore',
        'stats': stats,
        'recent_syncs': recent_syncs,
        'total_articles': total_articles,
        'published_articles': published_articles,
        'unpublished_articles': unpublished_articles,
    }
    
    return render(request, 'admin/ecommerce/sync_dashboard.html', context)
