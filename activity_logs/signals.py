from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ActivityLog
from .utils import log_activity


# ── Authentification ──────────────────────────────────────────────────────────

@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    log_activity(
        action=ActivityLog.LOGIN,
        module=ActivityLog.AUTH,
        description=f"Connexion de {user}",
        user=user,
        ip_address=(
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        ),
    )


# ── Factures ──────────────────────────────────────────────────────────────────

def _connect_facture():
    from factures.models import Facture

    @receiver(post_save, sender=Facture, weak=False)
    def on_facture_save(sender, instance, created, **kwargs):
        action = ActivityLog.CREATE if created else ActivityLog.UPDATE
        client = getattr(instance, 'client', None)
        desc = f"Facture #{instance.pk}"
        if client:
            desc += f" — {client}"
        log_activity(action=action, module=ActivityLog.FACTURES, description=desc)

    @receiver(post_delete, sender=Facture, weak=False)
    def on_facture_delete(sender, instance, **kwargs):
        log_activity(
            action=ActivityLog.DELETE,
            module=ActivityLog.FACTURES,
            description=f"Facture #{instance.pk} supprimée",
        )


# ── Caisse ────────────────────────────────────────────────────────────────────

def _connect_caisse():
    from caisse.models import CaisseCourante, MouvementCaisse

    @receiver(post_save, sender=CaisseCourante, weak=False)
    def on_caisse_save(sender, instance, created, **kwargs):
        if created:
            log_activity(
                action=ActivityLog.OPEN,
                module=ActivityLog.CAISSE,
                description=f"Caisse ouverte : {instance.caisse.nom}",
                user=instance.ouvert_par,
            )
        elif not instance.est_ouverte and instance.ferme_par:
            log_activity(
                action=ActivityLog.CLOSE,
                module=ActivityLog.CAISSE,
                description=f"Caisse clôturée : {instance.caisse.nom}",
                user=instance.ferme_par,
            )

    @receiver(post_save, sender=MouvementCaisse, weak=False)
    def on_mouvement_caisse(sender, instance, created, **kwargs):
        if not created:
            return
        direction = "Entrée" if instance.type_mouvement == "ENTREE" else "Sortie"
        desc = (
            f"{direction} — {instance.rubrique} — "
            f"{instance.montant} FC ({instance.caisse.caisse.nom})"
        )
        log_activity(
            action=ActivityLog.CREATE,
            module=ActivityLog.CAISSE,
            description=desc,
            user=instance.effectue_par,
        )


# ── Commandes ─────────────────────────────────────────────────────────────────

def _connect_commandes():
    from commandes.models import Commande

    @receiver(post_save, sender=Commande, weak=False)
    def on_commande_save(sender, instance, created, **kwargs):
        if not created:
            return
        fournisseur = getattr(instance, 'fournisseur', None)
        desc = f"Commande #{instance.pk}"
        if fournisseur:
            desc += f" — {fournisseur}"
        log_activity(action=ActivityLog.CREATE, module=ActivityLog.COMMANDES, description=desc)


# ── Approvisionnements ────────────────────────────────────────────────────────

def _connect_approvisionnements():
    from approvisionnements.models import Approvisionnement

    @receiver(post_save, sender=Approvisionnement, weak=False)
    def on_appro_save(sender, instance, created, **kwargs):
        if not created:
            return
        fournisseur = getattr(instance, 'fournisseur', '')
        desc = f"Approvisionnement #{instance.pk} — {fournisseur}"
        log_activity(
            action=ActivityLog.CREATE,
            module=ActivityLog.APPROVISIONNEMENTS,
            description=desc,
        )


# ── Stock / Transferts ────────────────────────────────────────────────────────

def _connect_stock():
    from produits.models import MouvementStock

    @receiver(post_save, sender=MouvementStock, weak=False)
    def on_mouvement_stock(sender, instance, created, **kwargs):
        if not created:
            return
        type_label = "Entrée" if instance.type == MouvementStock.IN else "Sortie"
        article = getattr(instance.article, 'designation', instance.article)
        magasin = getattr(instance.magasin, 'nom', instance.magasin)
        desc = f"{type_label} stock — {article} (x{instance.qte}) — {magasin}"
        log_activity(action=ActivityLog.CREATE, module=ActivityLog.STOCK, description=desc)


def connect_all():
    """Called from AppConfig.ready() to connect all signal handlers."""
    _connect_facture()
    _connect_caisse()
    _connect_commandes()
    _connect_approvisionnements()
    _connect_stock()
