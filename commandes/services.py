"""
commandes/services.py

Toute la logique métier du module commandes.
Chaque service = une action nommée par un verbe.
Chaque service qui écrit en DB est @transaction.atomic.
"""

from dataclasses import dataclass

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from users.models import CustomUser

from .exceptions import CommandeDejaClotureError
from .inputs import (
    ArticleCommandeAddInput,
    ArticleCommandeUpdateInput,
    CommandeCreateInput,
    CommandeUpdateInput,
)
from .models import Commande, DetailsCommande


# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class CommandeResult:
    commande: Commande


@dataclass
class DetailCommandeResult:
    detail: DetailsCommande
    merged: bool  # True si l'article existait déjà et la quantité a été fusionnée


# ── Helpers privés ────────────────────────────────────────────────────────────

def _generate_numero() -> int:
    """
    Génère le prochain numéro de commande, sans risque de race condition.
    Format initial : YY0001 (ex: 260001 pour 2026).
    Ensuite : dernier numéro + 1.
    select_for_update() pose un verrou sur les lignes lues — appelé
    uniquement depuis un service @transaction.atomic.
    """
    last_num = (
        Commande.objects
        .select_for_update()
        .aggregate(Max('numero'))['numero__max']
    )
    if last_num is None:
        year_suffix = str(timezone.now().year)[2:]
        return int(year_suffix + '0001')
    return last_num + 1


# ── Services ──────────────────────────────────────────────────────────────────

@transaction.atomic
def creer_commande(
    *,
    data: CommandeCreateInput,
    current_user: CustomUser,
) -> CommandeResult:
    commande = Commande.objects.create(
        numero=_generate_numero(),
        date_commande=data.date_commande,
        fournisseur_id=data.fournisseur_id,
        devise_id=data.devise_id,
        taux=data.taux,
        cree_par=current_user,
    )
    return CommandeResult(commande=commande)


@transaction.atomic
def modifier_commande(
    *,
    data: CommandeUpdateInput,
    current_user: CustomUser,
) -> CommandeResult:
    commande = Commande.objects.select_for_update().get(id=data.commande_id)
    commande.date_commande = data.date_commande
    commande.fournisseur_id = data.fournisseur_id
    commande.devise_id = data.devise_id
    commande.taux = data.taux
    commande.modifie_par = current_user
    commande.save(update_fields=[
        'date_commande', 'fournisseur', 'devise', 'taux',
        'modifie_par', 'date_modification',
    ])
    return CommandeResult(commande=commande)


@transaction.atomic
def cloturer_commande(
    *,
    commande_id: int,
    current_user: CustomUser,
) -> Commande:
    commande = Commande.objects.select_for_update().get(id=commande_id)
    if not commande.actif:
        raise CommandeDejaClotureError(
            f"La commande {commande.numero} est déjà clôturée."
        )
    commande.actif = False
    commande.modifie_par = current_user
    commande.save(update_fields=['actif', 'modifie_par', 'date_modification'])
    return commande


@transaction.atomic
def annuler_commande(
    *,
    commande_id: int,
    current_user: CustomUser,
) -> None:
    """
    Suppression physique — exception explicite à la règle logique du projet.
    Les commandes sont supprimées pour ne pas polluer l'historique.
    Les DetailsCommande en cascade (FK PROTECT → supprimés manuellement d'abord).
    """
    commande = Commande.objects.select_for_update().get(id=commande_id)
    commande.detailscommande_set.all().delete()
    commande.delete()


@transaction.atomic
def ajouter_article_commande(
    *,
    data: ArticleCommandeAddInput,
    current_user: CustomUser,
) -> DetailCommandeResult:
    """
    Ajoute un article à une commande.
    Si l'article est déjà présent, fusionne la quantité (pas de doublon).
    """
    commande = Commande.objects.select_for_update().get(id=data.commande_id)

    existing = (
        DetailsCommande.objects
        .filter(commande=commande, article_id=data.article_id)
        .first()
    )

    if existing:
        existing.qte += data.qte
        existing.save(update_fields=['qte', 'date_modification'])
        return DetailCommandeResult(detail=existing, merged=True)

    detail = DetailsCommande.objects.create(
        commande=commande,
        article_id=data.article_id,
        qte=data.qte,
        prix=data.prix,
    )
    return DetailCommandeResult(detail=detail, merged=False)


@transaction.atomic
def modifier_article_commande(
    *,
    data: ArticleCommandeUpdateInput,
    current_user: CustomUser,
) -> DetailsCommande:
    detail = DetailsCommande.objects.select_for_update().get(id=data.detail_id)
    detail.qte = data.qte
    detail.prix = data.prix
    detail.save(update_fields=['qte', 'prix', 'date_modification'])
    return detail


@transaction.atomic
def supprimer_article_commande(
    *,
    detail_id: int,
    current_user: CustomUser,
) -> None:
    """
    Suppression physique d'une ligne — DetailsCommande n'a pas de champ actif.
    Seule la Commande elle-même est soumise à la règle de suppression logique.
    """
    detail = DetailsCommande.objects.select_for_update().get(id=detail_id)
    detail.delete()
