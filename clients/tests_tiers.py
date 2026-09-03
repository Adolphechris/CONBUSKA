from decimal import Decimal
from datetime import date

import pytest
from django.test import TestCase
from django.db import IntegrityError

from fournisseurs.models import Fournisseur
from creanciers.models import Creancier, Debiteur


class TestFournisseurModel(TestCase):
    def test_fournisseur_creation_auto_code(self):
        f = Fournisseur.objects.create(
            nom="Fournisseur A", email="a@test.com",
            adresse="123 Rue", telephone="123", ville="Kin"
        )
        self.assertEqual(f.code, 2000)

    def test_fournisseur_auto_code_increment(self):
        Fournisseur.objects.create(
            code=2005, nom="F1", email="f1@t.com",
            adresse="Rue", telephone="1", ville="V"
        )
        f2 = Fournisseur.objects.create(
            nom="F2", email="f2@t.com",
            adresse="Rue", telephone="2", ville="V"
        )
        self.assertEqual(f2.code, 2006)

    def test_fournisseur_unique_nom(self):
        Fournisseur.objects.create(
            code=2001, nom="Dup", email="d1@t.com",
            adresse="R", telephone="1", ville="V"
        )
        with self.assertRaises(IntegrityError):
            Fournisseur.objects.create(
                code=2002, nom="Dup", email="d2@t.com",
                adresse="R", telephone="2", ville="V"
            )


class TestCreancierModel(TestCase):
    def test_creancier_creation_auto_code(self):
        c = Creancier.objects.create(
            nom="Creancier A", email="a@test.com",
            adresse="123 Rue", telephone="123", ville="Kin"
        )
        self.assertEqual(c.code, 4000)

    def test_creancier_auto_code_increment(self):
        Creancier.objects.create(
            code=4005, nom="C1", email="c1@t.com",
            adresse="R", telephone="1", ville="V"
        )
        c2 = Creancier.objects.create(
            nom="C2", email="c2@t.com",
            adresse="R", telephone="2", ville="V"
        )
        self.assertEqual(c2.code, 4006)


class TestDebiteurModel(TestCase):
    def test_debiteur_creation_auto_code(self):
        d = Debiteur.objects.create(
            nom="Debiteur A", email="a@test.com",
            adresse="123 Rue", telephone="123", ville="Kin"
        )
        self.assertEqual(d.code, 5000)

    def test_debiteur_auto_code_increment(self):
        Debiteur.objects.create(
            code=5005, nom="D1", email="d1@t.com",
            adresse="R", telephone="1", ville="V"
        )
        d2 = Debiteur.objects.create(
            nom="D2", email="d2@t.com",
            adresse="R", telephone="2", ville="V"
        )
        self.assertEqual(d2.code, 5006)
