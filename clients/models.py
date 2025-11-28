from django.db import models
from django.urls import reverse
from django.db.models import F, Sum
from factures.models import Facture, FactureClient
from caisse.models import MouvementCaisseClient
import decimal


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

    def total_factures(self):
        total = sum(i.facture.total for i in self.factures())
        return total


    def total_paiements(self):
        return self.paiements().aggregate(total=Sum('mouvement_caisse__montant'))['total'] or 0


    def solde(self):
        return self.total_factures() - self.total_paiements()


    @property
    def get_next_code(self):
        last_code = Client.objects.all().order_by('-code')[:1]
        try:
            code = [i.code + 1 for i in last_code][0]
        except IndexError:
            code = 3000
        return code

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code

        super(Client, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('client_details', args=[self.pk])
