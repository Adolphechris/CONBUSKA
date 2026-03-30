import datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone

from approvisionnements.models import Approvisionnement, DetailsApprovisionnement
from caisse.models import Caisse, CaisseCourante, MouvementCaisse, RubriqueCaisse
from factures.models import DetailsFacture, Facture
from factures.tests.factories import (
    ArticleFactory,
    ClientFactory,
    DetailsFactureFactory,
    FactureClientFactory,
    FactureFactory,
)
from parametres.models import Magasin, TauxEchange
from patrimoine.models import SnapshotJournalier
from produits.models import Article, Categorie, Unite
from fournisseurs.models import Fournisseur
from rapports.views import (
    RapportCaisseView,
    RapportResultatView,
    export_rapport_caisse_pdf,
)

User = get_user_model()


class RapportResultatViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="rapport_test",
            password="testpass123",
            force_password_change=False,
        )
        self.magasin = Magasin.objects.create(
            nom="Magasin principal",
            description="Magasin de test",
            localisation="Kinshasa",
            is_principal=True,
        )
        TauxEchange.objects.create(
            devise_source="USD",
            devise_cible="CDF",
            taux=Decimal("2800.00"),
            effective_date=timezone.now().date(),
        )
        self.categorie = Categorie.objects.create(nom="Categorie rapport")
        self.unite = Unite.objects.create(nom="Piece")
        self.fournisseur = Fournisseur.objects.create(
            code=9001,
            nom="Fournisseur rapport",
            email="fournisseur.rapport@test.com",
            adresse="Adresse test",
            telephone="0000000000",
            ville="Kinshasa",
            pays="RDC",
            tuteur="Tuteur",
            rccm="RCCM9001",
            id_nat="IDNAT9001",
            impot="0",
            tva="0",
            is_system=False,
            actif=True,
        )
        self.article_appro = Article.objects.create(
            code=9001,
            designation="Article appro",
            description="Article pour appros",
            categorie=self.categorie,
            unite=self.unite,
            fournisseur=self.fournisseur,
            prix_achat=Decimal("80.00"),
            prix_vente=Decimal("120.00"),
            prix_vente_gros=Decimal("110.00"),
            devise="FC",
            seuil=10,
            seuil_gros=50,
            emplacement="A1",
            actif=True,
        )
        self.article_vente = Article.objects.create(
            code=9002,
            designation="Article vente",
            description="Article pour ventes",
            categorie=self.categorie,
            unite=self.unite,
            fournisseur=self.fournisseur,
            prix_achat=Decimal("50.00"),
            prix_vente=Decimal("90.00"),
            prix_vente_gros=Decimal("85.00"),
            devise="FC",
            seuil=10,
            seuil_gros=50,
            emplacement="A2",
            actif=True,
        )

    def _create_view(self, debut, fin):
        request = self.factory.get(
            "/rapports/resultats/",
            {"debut": debut.isoformat(), "fin": fin.isoformat()},
        )
        request.user = self.user
        view = RapportResultatView()
        view.request = request
        return view

    def _create_approvisionnement(self, *, article, qte, prix, date_creation):
        appro = Approvisionnement.objects.create(
            numero=9100 + Approvisionnement.objects.count(),
            magasin=self.magasin,
            devise="FC",
            taux=Decimal("1.00"),
            cree_par=self.user,
            valide=True,
        )
        Approvisionnement.objects.filter(pk=appro.pk).update(
            date_creation=date_creation
        )
        appro.refresh_from_db()
        DetailsApprovisionnement.objects.create(
            approvisionnement=appro,
            fournisseur=self.fournisseur,
            facture=f"FACT-{appro.numero}",
            article=article,
            qte=qte,
            prix=prix,
        )

    def _create_facture(self, *, article, qte, prix, date_facture):
        facture = Facture.objects.create(
            numero=9200 + Facture.objects.count(),
            date_facture=date_facture,
            devise="FC",
            taux=Decimal("1.00"),
            remise=Decimal("0"),
            client_comptoir="Client comptoir",
            cree_par=self.user,
            valide=True,
            actif=False,
        )
        DetailsFacture.objects.create(
            facture=facture,
            article=article,
            qte=qte,
            prix=prix,
        )

    def test_resultat_par_article_repose_uniquement_sur_les_appros(self):
        today = timezone.now().date()
        self._create_approvisionnement(
            article=self.article_appro,
            qte=2,
            prix=Decimal("80.00"),
            date_creation=timezone.now(),
        )
        self._create_facture(
            article=self.article_appro,
            qte=1,
            prix=Decimal("140.00"),
            date_facture=today,
        )
        self._create_facture(
            article=self.article_vente,
            qte=3,
            prix=Decimal("90.00"),
            date_facture=today,
        )

        view = self._create_view(today.replace(day=1), today)
        context = view.get_context_data()

        self.assertEqual(context["total_ventes"], Decimal("180"))
        self.assertEqual(context["total_appros"], Decimal("80"))
        self.assertEqual(context["total_global"], Decimal("80"))
        self.assertEqual(len(context["resultat_articles"]), 1)
        self.assertEqual(
            context["resultat_articles"][0]["designation"],
            "Article appro",
        )
        self.assertEqual(
            context["resultat_articles"][0]["resultat"],
            Decimal("80"),
        )
        self.assertEqual(
            context["resultat_articles"][0]["pourcentage"],
            100.0,
        )

    def test_resultat_par_article_ignore_les_appros_hors_periode(self):
        today = timezone.now().date()
        hors_periode = timezone.now() - datetime.timedelta(days=40)
        self._create_approvisionnement(
            article=self.article_appro,
            qte=2,
            prix=Decimal("80.00"),
            date_creation=hors_periode,
        )

        view = self._create_view(today.replace(day=1), today)
        context = view.get_context_data()

        self.assertEqual(context["total_appros"], 0)
        self.assertEqual(context["total_global"], 0)
        self.assertEqual(context["resultat_articles"], [])


class RapportCaisseViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="rapport_caisse_test",
            password="testpass123",
            force_password_change=False,
        )
        self.caisse_principale = Caisse.objects.create(
            nom="Caisse principale",
            is_principal=True,
        )
        self.caisse_secondaire = Caisse.objects.create(
            nom="Caisse secondaire",
            is_principal=False,
        )
        self.session_principale = CaisseCourante.objects.create(
            caisse=self.caisse_principale,
            ouvert_par=self.user,
            solde_initial=Decimal("800.00"),
            est_ouverte=True,
        )
        self.session_secondaire = CaisseCourante.objects.create(
            caisse=self.caisse_secondaire,
            ouvert_par=self.user,
            solde_initial=Decimal("200.00"),
            est_ouverte=True,
        )
        self.today = timezone.now().date()
        SnapshotJournalier.objects.create(
            date=self.today,
            caisse=self.caisse_principale,
            total_entrees=Decimal("150.00"),
            total_sorties=Decimal("10.00"),
            solde_ouverture=Decimal("860.00"),
            solde_fermeture=Decimal("1000.00"),
            est_cloture=False,
        )
        SnapshotJournalier.objects.create(
            date=self.today,
            caisse=self.caisse_secondaire,
            total_entrees=Decimal("0.00"),
            total_sorties=Decimal("0.00"),
            solde_ouverture=Decimal("200.00"),
            solde_fermeture=Decimal("200.00"),
            est_cloture=False,
        )
        self.article = ArticleFactory(
            devise="FC",
            prix_achat=Decimal("40.00"),
            prix_vente=Decimal("60.00"),
        )
        self.client_maison = ClientFactory()
        self.rubrique_divers = RubriqueCaisse.objects.create(
            nom="Divers rapport",
            description="Rubrique de test",
            visible=True,
        )

    def _create_view(self):
        request = self.factory.get(
            "/rapports/caisses/",
            {"debut": self.today.isoformat(), "fin": self.today.isoformat()},
        )
        request.user = self.user
        view = RapportCaisseView()
        view.request = request
        return view

    def _create_comptoir_facture(self):
        facture = FactureFactory(
            cree_par=self.user,
            valide=True,
            client_comptoir="Client comptoir",
            date_facture=self.today,
            devise="FC",
            taux=Decimal("1.00"),
        )
        DetailsFactureFactory(
            facture=facture,
            article=self.article,
            qte=2,
            prix=Decimal("60.00"),
        )
        return facture

    def _create_client_maison_facture(self):
        facture = FactureFactory(
            cree_par=self.user,
            valide=True,
            client_comptoir=None,
            date_facture=self.today,
            devise="FC",
            taux=Decimal("1.00"),
        )
        FactureClientFactory(
            facture=facture,
            client=self.client_maison,
        )
        DetailsFactureFactory(
            facture=facture,
            article=self.article,
            qte=3,
            prix=Decimal("50.00"),
        )
        return facture

    def test_rapport_caisse_aligne_le_solde_reel_et_exclut_les_clients_maison(
        self,
    ):
        MouvementCaisse.objects.create(
            caisse=self.session_principale,
            type_mouvement="ENTREE",
            rubrique=self.rubrique_divers,
            montant=Decimal("30.00"),
            motif="Versement",
            effectue_par=self.user,
        )
        MouvementCaisse.objects.create(
            caisse=self.session_principale,
            type_mouvement="SORTIE",
            rubrique=self.rubrique_divers,
            montant=Decimal("10.00"),
            motif="Depense",
            effectue_par=self.user,
        )
        self._create_comptoir_facture()
        self._create_client_maison_facture()

        context = self._create_view().get_context_data()
        principale = next(
            item
            for item in context["solde_par_caisse"]
            if item["nom"] == "Caisse principale"
        )

        self.assertEqual(context["total_entrees"], Decimal("150.00"))
        self.assertEqual(context["total_sorties"], Decimal("10.00"))
        self.assertEqual(context["net_periode"], Decimal("140.00"))
        self.assertEqual(context["solde_total"], Decimal("1200.00"))
        self.assertEqual(principale["entrees"], Decimal("150.00"))
        self.assertEqual(principale["sorties"], Decimal("10.00"))
        self.assertEqual(principale["solde"], Decimal("1000.00"))

    @patch("rapports.views.DocumentGenerator.generate_rapport_caisse")
    def test_export_pdf_reutilise_la_meme_logique_que_la_vue(
        self,
        mock_generate_rapport_caisse,
    ):
        mock_generate_rapport_caisse.return_value = HttpResponse("ok")
        MouvementCaisse.objects.create(
            caisse=self.session_principale,
            type_mouvement="ENTREE",
            rubrique=self.rubrique_divers,
            montant=Decimal("30.00"),
            motif="Versement",
            effectue_par=self.user,
        )
        self._create_comptoir_facture()
        self._create_client_maison_facture()

        request = self.factory.get(
            "/rapports/caisses/pdf/",
            {"debut": self.today.isoformat(), "fin": self.today.isoformat()},
        )
        request.user = self.user

        response = export_rapport_caisse_pdf(request)

        self.assertEqual(response.status_code, 200)
        kwargs = mock_generate_rapport_caisse.call_args.kwargs
        principale = next(
            item
            for item in kwargs["solde_par_caisse"]
            if item["nom"] == "Caisse principale"
        )
        self.assertEqual(kwargs["total_entrees"], Decimal("150.00"))
        self.assertEqual(kwargs["total_sorties"], Decimal("0.00"))
        self.assertEqual(kwargs["net_periode"], Decimal("150.00"))
        self.assertEqual(kwargs["solde_total"], Decimal("1200.00"))
        self.assertEqual(principale["entrees"], Decimal("150.00"))
