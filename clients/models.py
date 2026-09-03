from django.db import models, transaction
from django.db.models import Max
from django.urls import reverse
from django.db.models import F, Sum
from factures.models import FactureClient
from caisse.models import MouvementCaisseClient


class Client(models.Model):
    code = models.IntegerField(unique=True, blank=False)
    photo = models.ImageField(upload_to='clients/', blank=True)
    nom = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    adresse = models.CharField(max_length=150)
    telephone = models.CharField(max_length=150)
    ville = models.CharField(max_length=30)

    objects = models.Manager()

    def __str__(self):
        return self.nom

    def factures(self):
        return FactureClient.objects.select_related('facture').filter(client=self)

    def paiements(self):
        return MouvementCaisseClient.objects.filter(client=self)

    def total_factures_usd(self):
        from decimal import Decimal
        return self.factures().filter(facture__valide=True).aggregate(
            total=Sum('facture__valeur_usd')
        )['total'] or Decimal('0')

    def total_paiements_usd(self):
        from decimal import Decimal
        return self.paiements().aggregate(total=Sum('valeur_usd'))['total'] or Decimal('0')

    def solde_usd(self):
        return self.total_factures_usd() - self.total_paiements_usd()

    def solde_fc(self):
        return self.total_factures() - self.total_paiements()

    def total_factures(self):
        from django.db.models import ExpressionWrapper, DecimalField
        return (
            self.factures()
            .filter(facture__valide=True)
            .aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('facture__valeur_usd') * F('facture__taux'),
                        output_field=DecimalField(max_digits=18, decimal_places=4)
                    )
                )
            )['total']
            or 0
        )

    def total_paiements(self):
        return self.paiements().aggregate(total=Sum('mouvement_caisse__montant'))['total'] or 0

    def solde(self):
        return self.solde_usd()


    @property
    def get_next_code(self):
        with transaction.atomic():
            last_code = Client.objects.select_for_update().aggregate(mcode=Max("code"))["mcode"]
        return (last_code + 1) if last_code else 3000

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code

        super(Client, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('client_details', args=[self.pk])
