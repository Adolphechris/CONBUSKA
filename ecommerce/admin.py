"""
Interface d'administration pour le module e-commerce.
Permet de:
- Voir l'état de synchronisation Firestore
- Déclencher une synchronisation manuelle
- Consulter les erreurs de synchronisation
- Voir les statistiques
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

from produits.models import Article
from .sync.services import FirestoreSyncService


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Admin pour les articles avec indicateur de synchronisation Firestore.
    """
    list_display = [
        'code',
        'designation',
        'categorie',
        'prix_vente',
        'devise',
        'stock_disponible',
        'est_publie',
        'derniere_sync_firestore',
        'sync_status_display',
    ]
    
    list_filter = [
        'est_publie',
        'actif',
        'categorie',
        'devise',
    ]
    
    search_fields = [
        'code',
        'designation',
        'description',
    ]
    
    readonly_fields = [
        'derniere_sync_firestore',
        'sync_status_display',
    ]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('code', 'designation', 'categorie', 'description', 'slug')
        }),
        ('Prix', {
            'fields': ('prix_achat', 'prix_vente', 'prix_vente_gros', 'devise')
        }),
        ('Stock', {
            'fields': ('seuil', 'seuil_gros', 'emplacement')
        }),
        ('Images', {
            'fields': ('photo1', 'photo2')
        }),
        ('Publication en ligne', {
            'fields': ('est_publie', 'actif', 'derniere_sync_firestore', 'sync_status_display')
        }),
    )
    
    actions = ['sync_to_firestore', 'force_sync_to_firestore']
    
    def stock_disponible(self, obj):
        """Affiche le stock disponible."""
        return obj.stock
    stock_disponible.short_description = 'Stock'
    stock_disponible.admin_order_field = 'stock'
    
    def sync_status_display(self, obj):
        """Affiche le statut de synchronisation."""
        if not obj.est_publie:
            return format_html('<span style="color: gray;">Non publié</span>')
        
        if not obj.derniere_sync_firestore:
            return format_html('<span style="color: orange;">Jamais synchronisé</span>')
        
        # Vérifier si la sync est récente (moins de 5 minutes)
        delta = timezone.now() - obj.derniere_sync_firestore
        if delta.total_seconds() < 300:
            return format_html('<span style="color: green;">✓ Synchronisé</span>')
        else:
            return format_html('<span style="color: orange;">⚠ Sync ancienne</span>')
    
    sync_status_display.short_description = 'Statut Firestore'
    
    @admin.action(description='Synchroniser vers Firestore')
    def sync_to_firestore(self, request, queryset):
        """Synchronise les articles sélectionnés vers Firestore."""
        count = 0
        errors = 0
        
        for article in queryset.filter(est_publie=True):
            try:
                success = FirestoreSyncService.sync_article(article)
                if success:
                    count += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f"Erreur pour {article.designation}: {e}",
                    messages.ERROR
                )
        
        if count > 0:
            self.message_user(
                request,
                f"{count} article(s) synchronisé(s) avec succès.",
                messages.SUCCESS
            )
        
        if errors > 0:
            self.message_user(
                request,
                f"{errors} erreur(s) lors de la synchronisation.",
                messages.WARNING
            )
    
    @admin.action(description='Forcer synchronisation (écrase Firestore)')
    def force_sync_to_firestore(self, request, queryset):
        """Force la synchronisation même si l'article n'a pas été modifié."""
        count = 0
        errors = 0
        
        for article in queryset.filter(est_publie=True):
            try:
                success = FirestoreSyncService.sync_article(article, force=True)
                if success:
                    count += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f"Erreur pour {article.designation}: {e}",
                    messages.ERROR
                )
        
        if count > 0:
            self.message_user(
                request,
                f"{count} article(s) synchronisé(s) avec succès (force).",
                messages.SUCCESS
            )
        
        if errors > 0:
            self.message_user(
                request,
                f"{errors} erreur(s) lors de la synchronisation.",
                messages.WARNING
            )


# Ajouter une vue personnalisée pour le dashboard de synchronisation
def sync_dashboard_view(request):
    """Vue du dashboard de synchronisation Firestore."""
    
    # Récupérer les statistiques
    stats = FirestoreSyncService.get_sync_stats()
    
    # Récupérer les articles récemment synchronisés
    from .models import Article
    recent_syncs = Article.objects.filter(
        derniere_sync_firestore__isnull=False
    ).order_by('-derniere_sync_firestore')[:10]
    
    # Compter les articles
    total_articles = Article.objects.count()
    published_articles = Article.objects.filter(est_publie=True).count()
    unpublished_articles = Article.objects.filter(est_publie=False).count()
    
    context = {
        'title': 'Dashboard Synchronisation Firestore',
        'stats': stats,
        'recent_syncs': recent_syncs,
        'total_articles': total_articles,
        'published_articles': published_articles,
        'unpublished_articles': unpublished_articles,
        'has_permission': True,
    }
    
    return render(request, 'admin/ecommerce/sync_dashboard.html', context)


# Ajouter l'URL au admin site
from django.contrib import admin as django_admin

# Enregistrer la vue personnalisée
django_admin.site.admin_view(sync_dashboard_view)

# Créer l'URL pattern
sync_dashboard_url = path(
    'ecommerce/sync-dashboard/',
    django_admin.site.admin_view(sync_dashboard_view),
    name='ecommerce_sync_dashboard'
)

# Vue pour importer les commandes
def import_commandes_view(request):
    """Vue pour déclencher l'import des commandes."""
    from django.contrib import messages
    from ecommerce.sync.import_commandes import ImportCommandesService
    
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        try:
            limit = request.POST.get('limit')
            limit_int = int(limit) if limit else None
            
            resultat = ImportCommandesService.importer_commandes(limit=limit_int)
            
            if resultat['succes'] > 0:
                messages.success(
                    request,
                    f"Import terminé: {resultat['succes']} commande(s) importée(s), "
                    f"{resultat['erreurs']} erreur(s)"
                )
            else:
                messages.warning(
                    request,
                    f"Aucune commande importée. {resultat['erreurs']} erreur(s)."
                )
            
            # Stocker les détails dans la session pour affichage
            request.session['import_resultat'] = resultat
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'import: {e}")
    
    return redirect('ecommerce_sync_dashboard')

# Ajouter les URLs
from django.urls import path
from django.contrib import admin

urlpatterns_admin = [
    path('sync-dashboard/', admin.site.admin_view(sync_dashboard_view), name='ecommerce_sync_dashboard'),
    path('sync-dashboard/import/', admin.site.admin_view(import_commandes_view), name='ecommerce_import_commandes'),
]
