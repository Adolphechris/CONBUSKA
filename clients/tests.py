from decimal import Decimal
from datetime import date

import pytest
from django.test import TestCase
from django.db import transaction
from django.db import IntegrityError

from clients.models import Client
from fournisseurs.models import Fournisseur
from creanciers.models import Creancier, Debiteur
from django.contrib.auth import get_user_model

User = get_user_model()


class TestClientModel(TestCase):
    def test_client_creation_auto_code(self):
        c = Client.objects.create(
            nom="Test Client A", email="a@test.com",
            adresse="123 Rue", telephone="123", ville="Kin"
        )
        self.assertEqual(c.code, 3000)

    def test_client_auto_code_increment(self):
        Client.objects.create(
            code=3005, nom="C1", email="c1@t.com",
            adresse="Rue", telephone="1", ville="V"
        )
        c2 = Client.objects.create(
            nom="C2", email="c2@t.com",
            adresse="Rue", telephone="2", ville="V"
        )
        self.assertEqual(c2.code, 3006)

    def test_client_unique_nom(self):
        Client.objects.create(
            code=3001, nom="Dup", email="d1@t.com",
            adresse="R", telephone="1", ville="V"
        )
        with self.assertRaises(IntegrityError):
            Client.objects.create(
                code=3002, nom="Dup", email="d2@t.com",
                adresse="R", telephone="2", ville="V"
            )
