from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from users.models import CustomUser
from factures.models import Facture
from caisse.models import Caisse, CaisseCourante, RubriqueCaisse, MouvementCaisse, MouvementCaisseClient
from clients.models import Client
from parametres.models import TauxEchange
import datetime


class ImmutabilityTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='tester', password='pw')

    def test_facture_sets_valeur_usd_and_prevents_taux_change(self):
        # create non-validated invoice first (avoid querying related details before save)
        f = Facture.objects.create(numero=1111, devise='FC', taux=Decimal('2000'), valide=False, cree_par=self.user)
        # Now validate: set valide True and save (this will compute valeur_usd)
        f.valide = True
        f.save()
        f.refresh_from_db()
        # With no details total==0 so valeur_usd should be 0
        self.assertEqual(f.valeur_usd, Decimal('0'))

        # Attempt to change taux on a validated invoice should raise on full_clean
        f.taux = Decimal('2500')
        with self.assertRaises(ValidationError):
            f.full_clean()

    def test_mouvement_caisse_client_creates_historical_usd_and_prevents_change(self):
        caisse = Caisse.objects.create(nom='Tst Caisse', is_principal=True)
        cc = CaisseCourante.objects.create(caisse=caisse, solde_initial=Decimal('0'))
        rubrique = RubriqueCaisse.objects.create(nom='Test', description='x')
        client = Client.objects.create(code=9000, nom='C1', email='c1@example.com', adresse='here', telephone='000', ville='Nowhere')

        # Ensure an exchange rate exists for today
        today = datetime.date.today()
        TauxEchange.objects.create(devise_source='USD', devise_cible='CDF', taux=Decimal('2000.00'), effective_date=today)

        m = MouvementCaisse.objects.create(caisse=cc, type_mouvement='ENTREE', rubrique=rubrique, montant=Decimal('10000'), motif='t', effectue_par=self.user)
        mc = MouvementCaisseClient.objects.create(mouvement_caisse=m, client=client)
        mc.refresh_from_db()

        self.assertIsNotNone(mc.taux_paiement)
        self.assertIsNotNone(mc.valeur_usd)

        # Attempting to change stored USD should be rejected by full_clean
        original_val = mc.valeur_usd
        mc.valeur_usd = Decimal('9999')
        with self.assertRaises(ValidationError):
            mc.full_clean()

        # The save/update path preserves historical values; updating and saving should not alter stored values
        mc.valeur_usd = original_val
        mc.taux_paiement = mc.taux_paiement
        mc.save()
        mc.refresh_from_db()
        self.assertEqual(mc.valeur_usd, original_val)
