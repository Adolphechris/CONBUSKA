from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    # ── Actions ──────────────────────────────────────────────────────────────
    CREATE   = 'CREATE'
    UPDATE   = 'UPDATE'
    DELETE   = 'DELETE'
    OPEN     = 'OPEN'
    CLOSE    = 'CLOSE'
    TRANSFER = 'TRANSFER'
    LOGIN    = 'LOGIN'

    ACTION_CHOICES = [
        (CREATE,   'Création'),
        (UPDATE,   'Modification'),
        (DELETE,   'Suppression'),
        (OPEN,     'Ouverture'),
        (CLOSE,    'Clôture'),
        (TRANSFER, 'Transfert'),
        (LOGIN,    'Connexion'),
    ]

    # ── Modules ───────────────────────────────────────────────────────────────
    FACTURES          = 'factures'
    CAISSE            = 'caisse'
    COMMANDES         = 'commandes'
    APPROVISIONNEMENTS = 'approvisionnements'
    STOCK             = 'stock'
    AUTH              = 'auth'
    SYSTEM            = 'system'

    MODULE_CHOICES = [
        (FACTURES,           'Factures'),
        (CAISSE,             'Caisse'),
        (COMMANDES,          'Commandes'),
        (APPROVISIONNEMENTS, 'Approvisionnements'),
        (STOCK,              'Stock'),
        (AUTH,               'Authentification'),
        (SYSTEM,             'Système'),
    ]

    # ── Fields ────────────────────────────────────────────────────────────────
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='activity_logs',
    )
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module      = models.CharField(max_length=30, choices=MODULE_CHOICES)
    description = models.CharField(max_length=500)
    created_at  = models.DateTimeField(auto_now_add=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['module']),
            models.Index(fields=['action']),
        ]
        verbose_name = 'Journal d\'activité'
        verbose_name_plural = 'Journal d\'activités'

    def __str__(self):
        who = self.user or 'Système'
        return f"[{self.get_module_display()}] {self.get_action_display()} — {self.description} ({who})"

    # ── Template helpers ──────────────────────────────────────────────────────
    @property
    def icon(self):
        return {
            self.CREATE:   'fa-plus-circle',
            self.UPDATE:   'fa-pencil',
            self.DELETE:   'fa-trash-o',
            self.OPEN:     'fa-unlock',
            self.CLOSE:    'fa-lock',
            self.TRANSFER: 'fa-exchange',
            self.LOGIN:    'fa-sign-in',
        }.get(self.action, 'fa-circle')

    @property
    def color_class(self):
        return {
            self.CREATE:   'activity-success',
            self.UPDATE:   'activity-info',
            self.DELETE:   'activity-danger',
            self.OPEN:     'activity-success',
            self.CLOSE:    'activity-warning',
            self.TRANSFER: 'activity-primary',
            self.LOGIN:    'activity-success',
        }.get(self.action, 'activity-default')

    @property
    def module_icon(self):
        return {
            self.FACTURES:           'fa-file-text',
            self.CAISSE:             'fa-money',
            self.COMMANDES:          'fa-file-text-o',
            self.APPROVISIONNEMENTS: 'fa-truck',
            self.STOCK:              'fa-cubes',
            self.AUTH:               'fa-sign-in',
            self.SYSTEM:             'fa-cogs',
        }.get(self.module, 'fa-circle-o')
