"""
commandes/tests/test_services.py

Tests des services du module commandes.
Couvre : cas nominal, cas d'erreur métier, effets sur la DB.
"""

import datetime
from decimal import Decimal

import pytest

from commandes.exceptions import CommandeDejaClotureError
from commandes.inputs import (
    ArticleCommandeAddInput,
    ArticleCommandeUpdateInput,
    CommandeCreateInput,
    CommandeUpdateInput,
)
from commandes.models import Commande, DetailsCommande
from commandes.services import (
    ajouter_article_commande,
    annuler_commande,
    cloturer_commande,
    creer_commande,
    modifier_article_commande,
    modifier_commande,
    supprimer_article_commande,
)

from .factories import (
    ArticleFactory,
    CommandeFactory,
    CustomUserFactory,
    DetailsCommandeFactory,
    DeviseFactory,
    FournisseurFactory,
)


# ── creer_commande ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCreerCommande:
    def test_nominal(self):
        user = CustomUserFactory()
        fournisseur = FournisseurFactory()
        devise = DeviseFactory(code='USD')
        data = CommandeCreateInput(
            date_commande=datetime.date.today(),
            fournisseur_id=fournisseur.pk,
            devise_id=devise.pk,
            taux=Decimal('1.0000'),
        )
        result = creer_commande(data=data, current_user=user)
        assert result.commande.pk is not None
        assert result.commande.fournisseur == fournisseur
        assert result.commande.devise == devise
        assert result.commande.cree_par == user
        assert result.commande.actif is True

    def test_premier_numero_format_annee(self):
        """Sans commande existante, le numéro commence à YY0001."""
        user = CustomUserFactory()
        fournisseur = FournisseurFactory()
        data = CommandeCreateInput(
            date_commande=datetime.date.today(),
            fournisseur_id=fournisseur.pk,
            taux=Decimal('0'),
        )
        result = creer_commande(data=data, current_user=user)
        year_suffix = str(datetime.date.today().year)[2:]
        assert str(result.commande.numero).startswith(year_suffix)
        assert str(result.commande.numero).endswith('0001')

    def test_numero_incremente(self):
        """Le numéro suivant est toujours dernier + 1."""
        user = CustomUserFactory()
        fournisseur = FournisseurFactory()
        c1 = CommandeFactory(numero=260010, fournisseur=fournisseur)
        data = CommandeCreateInput(
            date_commande=datetime.date.today(),
            fournisseur_id=fournisseur.pk,
            taux=Decimal('0'),
        )
        result = creer_commande(data=data, current_user=user)
        assert result.commande.numero == c1.numero + 1

    def test_sans_devise(self):
        """La devise est optionnelle."""
        user = CustomUserFactory()
        fournisseur = FournisseurFactory()
        data = CommandeCreateInput(
            date_commande=datetime.date.today(),
            fournisseur_id=fournisseur.pk,
            taux=Decimal('0'),
            devise_id=None,
        )
        result = creer_commande(data=data, current_user=user)
        assert result.commande.devise is None


# ── modifier_commande ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestModifierCommande:
    def test_nominal(self):
        user = CustomUserFactory()
        commande = CommandeFactory(taux=Decimal('1.0000'))
        nouveau_fournisseur = FournisseurFactory()
        nouvelle_devise = DeviseFactory(code='EUR')
        data = CommandeUpdateInput(
            commande_id=commande.pk,
            date_commande=datetime.date(2026, 6, 1),
            fournisseur_id=nouveau_fournisseur.pk,
            taux=Decimal('2.5000'),
            devise_id=nouvelle_devise.pk,
        )
        result = modifier_commande(data=data, current_user=user)
        assert result.commande.fournisseur == nouveau_fournisseur
        assert result.commande.taux == Decimal('2.5000')
        assert result.commande.devise == nouvelle_devise
        assert result.commande.modifie_par == user

    def test_persiste_en_db(self):
        user = CustomUserFactory()
        commande = CommandeFactory()
        fournisseur = FournisseurFactory()
        data = CommandeUpdateInput(
            commande_id=commande.pk,
            date_commande=datetime.date(2026, 6, 1),
            fournisseur_id=fournisseur.pk,
            taux=Decimal('3.0000'),
            devise_id=None,
        )
        modifier_commande(data=data, current_user=user)
        commande.refresh_from_db()
        assert commande.taux == Decimal('3.0000')
        assert commande.fournisseur == fournisseur
        assert commande.devise is None

    def test_leve_does_not_exist_si_introuvable(self):
        user = CustomUserFactory()
        fournisseur = FournisseurFactory()
        with pytest.raises(Commande.DoesNotExist):
            modifier_commande(
                data=CommandeUpdateInput(
                    commande_id=99999,
                    date_commande=datetime.date.today(),
                    fournisseur_id=fournisseur.pk,
                    taux=Decimal('1.0000'),
                ),
                current_user=user,
            )


# ── cloturer_commande ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCloturerCommande:
    def test_nominal(self):
        user = CustomUserFactory()
        commande = CommandeFactory(actif=True)
        result = cloturer_commande(commande_id=commande.pk, current_user=user)
        assert result.actif is False
        assert result.modifie_par == user

    def test_persiste_en_db(self):
        user = CustomUserFactory()
        commande = CommandeFactory(actif=True)
        cloturer_commande(commande_id=commande.pk, current_user=user)
        commande.refresh_from_db()
        assert commande.actif is False

    def test_leve_erreur_si_deja_cloturee(self):
        user = CustomUserFactory()
        commande = CommandeFactory(actif=False)
        with pytest.raises(CommandeDejaClotureError):
            cloturer_commande(commande_id=commande.pk, current_user=user)


# ── annuler_commande ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnnulerCommande:
    def test_supprime_la_commande(self):
        user = CustomUserFactory()
        commande = CommandeFactory()
        pk = commande.pk
        annuler_commande(commande_id=pk, current_user=user)
        assert not Commande.objects.filter(pk=pk).exists()

    def test_supprime_les_lignes_en_cascade(self):
        user = CustomUserFactory()
        commande = CommandeFactory()
        detail = DetailsCommandeFactory(commande=commande)
        annuler_commande(commande_id=commande.pk, current_user=user)
        assert not DetailsCommande.objects.filter(pk=detail.pk).exists()

    def test_leve_does_not_exist_si_introuvable(self):
        user = CustomUserFactory()
        with pytest.raises(Commande.DoesNotExist):
            annuler_commande(commande_id=99999, current_user=user)


# ── ajouter_article_commande ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestAjouterArticleCommande:
    def test_nominal_nouvel_article(self):
        user = CustomUserFactory()
        commande = CommandeFactory()
        article = ArticleFactory()
        data = ArticleCommandeAddInput(
            commande_id=commande.pk,
            article_id=article.pk,
            qte=3,
            prix=Decimal('50.00'),
        )
        result = ajouter_article_commande(data=data, current_user=user)
        assert result.merged is False
        assert result.detail.qte == 3
        assert result.detail.prix == Decimal('50.00')
        assert DetailsCommande.objects.filter(commande=commande).count() == 1

    def test_doublon_fusionne_la_quantite(self):
        """Ajouter le même article deux fois incrémente la qte, sans doublon."""
        user = CustomUserFactory()
        commande = CommandeFactory()
        article = ArticleFactory()
        existing = DetailsCommandeFactory(commande=commande, article=article, qte=2)
        data = ArticleCommandeAddInput(
            commande_id=commande.pk,
            article_id=article.pk,
            qte=5,
            prix=Decimal('50.00'),
        )
        result = ajouter_article_commande(data=data, current_user=user)
        assert result.merged is True
        assert result.detail.pk == existing.pk
        existing.refresh_from_db()
        assert existing.qte == 7  # 2 + 5
        assert DetailsCommande.objects.filter(commande=commande).count() == 1

    def test_deux_articles_differents_creent_deux_lignes(self):
        user = CustomUserFactory()
        commande = CommandeFactory()
        a1 = ArticleFactory()
        a2 = ArticleFactory()
        for article in (a1, a2):
            ajouter_article_commande(
                data=ArticleCommandeAddInput(
                    commande_id=commande.pk,
                    article_id=article.pk,
                    qte=1,
                    prix=Decimal('10.00'),
                ),
                current_user=user,
            )
        assert DetailsCommande.objects.filter(commande=commande).count() == 2


# ── modifier_article_commande ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestModifierArticleCommande:
    def test_nominal(self):
        user = CustomUserFactory()
        detail = DetailsCommandeFactory(qte=3, prix=Decimal('50.00'))
        data = ArticleCommandeUpdateInput(
            detail_id=detail.pk,
            qte=10,
            prix=Decimal('75.00'),
        )
        result = modifier_article_commande(data=data, current_user=user)
        assert result.qte == 10
        assert result.prix == Decimal('75.00')

    def test_persiste_en_db(self):
        user = CustomUserFactory()
        detail = DetailsCommandeFactory(qte=3, prix=Decimal('50.00'))
        modifier_article_commande(
            data=ArticleCommandeUpdateInput(
                detail_id=detail.pk, qte=10, prix=Decimal('75.00')
            ),
            current_user=user,
        )
        detail.refresh_from_db()
        assert detail.qte == 10
        assert detail.prix == Decimal('75.00')

    def test_leve_does_not_exist_si_introuvable(self):
        user = CustomUserFactory()
        with pytest.raises(DetailsCommande.DoesNotExist):
            modifier_article_commande(
                data=ArticleCommandeUpdateInput(
                    detail_id=99999, qte=1, prix=Decimal('1.00')
                ),
                current_user=user,
            )


# ── supprimer_article_commande ────────────────────────────────────────────────

@pytest.mark.django_db
class TestSupprimerArticleCommande:
    def test_nominal(self):
        user = CustomUserFactory()
        commande = CommandeFactory()
        detail = DetailsCommandeFactory(commande=commande)
        supprimer_article_commande(detail_id=detail.pk, current_user=user)
        assert not DetailsCommande.objects.filter(pk=detail.pk).exists()

    def test_ne_supprime_pas_les_autres_lignes(self):
        user = CustomUserFactory()
        commande = CommandeFactory()
        d1 = DetailsCommandeFactory(commande=commande)
        d2 = DetailsCommandeFactory(commande=commande)
        supprimer_article_commande(detail_id=d1.pk, current_user=user)
        assert DetailsCommande.objects.filter(pk=d2.pk).exists()

    def test_leve_does_not_exist_si_introuvable(self):
        user = CustomUserFactory()
        with pytest.raises(DetailsCommande.DoesNotExist):
            supprimer_article_commande(detail_id=99999, current_user=user)
