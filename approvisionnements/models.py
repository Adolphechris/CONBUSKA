from django.db import models
from django.urls import reverse
from django.forms.models import model_to_dict
from django.db import transaction
from common.utils import is_duplicate
from produits.models import Stock
import datetime


class Approvisionnement(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    numero = models.IntegerField(unique=True, blank=False)
    magasin = models.ForeignKey('parametres.Magasin', on_delete=models.PROTECT, null=False)
    devise = models.CharField(max_length=2, choices=DEVISES)
    taux = models.DecimalField(default=0.0, max_digits=6, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey('users.CustomUser',
                                 related_name='approvisionnementcreepar',
                                 on_delete=models.PROTECT)
    modifie_par = models.ForeignKey('users.CustomUser',
                                    blank=True, null=True,
                                    related_name='approvisionnementmodpar',
                                    on_delete=models.PROTECT)
    actif = models.BooleanField(default=True)

    objects = models.Manager()

    def __str__(self):
        return self.numero

    @property
    def total_approvisionnement(self):
        details_approvisionnement = DetailsApprovisionnement.objects.filter(approvisionnement=self.pk)
        total = sum(i.prix_total for i in details_approvisionnement)
        return total

    @property
    def get_next_num(self):
        last_num = Approvisionnement.objects.all().order_by('-numero')[:1]
        try:
            numero = [i.numero + 1 for i in last_num][0]
        except IndexError:
            numero = int(str(datetime.datetime.now().year)[2:] + '0000')
        return numero

    def save(self, *args, **kwargs):
        if self.numero is None:
            self.numero = self.get_next_num

        super(Approvisionnement, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('approvisionnement_details', args=[self.pk])


class DetailsApprovisionnement(models.Model):
    approvisionnement = models.ForeignKey(Approvisionnement, on_delete=models.PROTECT, null=True)
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.PROTECT, null=False)
    facture = models.CharField(max_length=15)
    declaration = models.DecimalField(max_digits=8, decimal_places=4)
    transport = models.DecimalField(max_digits=8, decimal_places=4)
    tva = models.DecimalField(max_digits=8, decimal_places=4)
    manutention = models.DecimalField(max_digits=8, decimal_places=4)
    autre_frais = models.DecimalField(max_digits=8, decimal_places=4)
    article = models.ForeignKey('produits.Article', on_delete=models.PROTECT, null=True)
    qte = models.IntegerField()
    prix = models.DecimalField(max_digits=8, decimal_places=4)
    date_peremption = models.DateField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    @property
    def prix_total(self):
        return self.qte * self.prix

    @property
    def frais_achat(self):
        total = self.declaration + self.transport + self.tva + self.manutention + self.autre_frais
        return total

    @property
    def cout_achat(self):
        total = self.prix + self.frais_achat
        return total

    @property
    def prix_vente(self):
        prix_vente_fc, prix_vente_usd = self.article.prix_vente_devise
        if self.approvisionnement.devise == '$':
            return prix_vente_usd
        else:
            return prix_vente_fc

    @property
    def prix_vente_gros(self):
        prix_vente_gros_fc, prix_vente_gros_usd = self.article.prix_vente_gros_devise
        if self.approvisionnement.devise == '$':
            return prix_vente_gros_usd
        else:
            return prix_vente_gros_fc

    @property
    def resultat(self):
        prix_vente_fc, prix_vente_usd = self.article.prix_vente_devise
        if self.approvisionnement.devise == '$':
            return (prix_vente_usd - self.cout_achat) * self.qte
        else:
            return (prix_vente_fc - self.cout_achat) * self.qte

    @transaction.atomic
    def add_details(self):
        detail, created = DetailsApprovisionnement.objects.get_or_create(
            approvisionnement=self.approvisionnement.pk,
            article=self.article.pk,
            date_peremption=self.date_peremption,
            fournisseur=self.fournisseur.pk,
            facture=self.facture,
            defaults={
                'declaration': self.declaration,
                'transport': self.transport,
                'tva': self.tva,
                'manutention': self.manutention,
                'autre_frais': self.autre_frais,
                'qte': self.qte,
                'prix': self.prix,
            }
        )

        if not created:
            detail.qte += self.qte
            detail.save()

    def update(self, old_object):
        # First remove old object in the stock
        get_stock = Stock.objects.get(magasin=self.approvisionnement.magasin, article=self.article,
                                      date_peremption=old_object.date_peremption)
        get_stock.remove(old_object.qte)

        # Find if duplicate
        data = {'article': self.article.pk, 'date_peremption': self.date_peremption}
        items = DetailsApprovisionnement.objects.filter(approvisionnement=self.approvisionnement.pk)
        items_to_dict = [model_to_dict(i) for i in items]

        duplicate = is_duplicate(items_to_dict, data)
        if duplicate:
            # Merge
            duplicated_line = DetailsApprovisionnement.objects.get(id=duplicate['id'])
            duplicated_line.qte += self.qte
            duplicated_line.save()

            # Remove
            old_object.delete()
        else:
            self.save()

    def save(self, *args, **kwargs):
        stock = Stock(
            magasin=self.approvisionnement.magasin,
            article=self.article,
            qte=self.qte,
            date_peremption=self.date_peremption
        )
        stock.add_stock()

        super(DetailsApprovisionnement, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('approvisionnement_details', args=[self.approvisionnement.pk])
