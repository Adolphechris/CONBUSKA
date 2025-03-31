from django.db import models
from django.urls import reverse
from django.forms.models import model_to_dict
from common.utils import is_duplicate
import datetime


class Commande(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    numero = models.IntegerField(unique=True, blank=False)
    date_commande = models.DateField()
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.PROTECT, null=False)
    devise = models.CharField(max_length=2, choices=DEVISES)
    taux = models.DecimalField(default=0.0, max_digits=6, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey('users.CustomUser',
                                 related_name='commandecreepar',
                                 on_delete=models.PROTECT)
    modifie_par = models.ForeignKey('users.CustomUser',
                                    blank=True, null=True,
                                    related_name='commandemodpar',
                                    on_delete=models.PROTECT)
    actif = models.BooleanField(default=True)

    objects = models.Manager()

    def __str__(self):
        return self.numero

    @property
    def total_commande(self):
        details_commande = DetailsCommande.objects.filter(commande=self.pk)
        total = sum(i.prix_total for i in details_commande)
        return total

    @property
    def get_next_num(self):
        last_num = Commande.objects.all().order_by('-numero')[:1]
        try:
            numero = [i.numero + 1 for i in last_num][0]
        except IndexError:
            numero = int(str(datetime.datetime.now().year)[2:] + '0000')
        return numero

    def save(self, *args, **kwargs):
        if self.numero is None:
            self.numero = self.get_next_num

        super(Commande, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('commande_details', args=[self.pk])


class DetailsCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.PROTECT, null=True)
    article = models.ForeignKey('produits.Article', on_delete=models.PROTECT, null=True)
    qte = models.IntegerField()
    prix = models.DecimalField(default=0.0, max_digits=8, decimal_places=4)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    @property
    def prix_total(self):
        return self.qte * self.prix

    def valid(self):
        data = {'article': self.article.pk}
        items = DetailsCommande.objects.filter(commande=self.commande.pk)
        items_to_dict = [model_to_dict(i) for i in items]

        duplicate = is_duplicate(items_to_dict, data)
        if duplicate:
            duplicated_line = DetailsCommande.objects.get(id=duplicate['id'])
            duplicated_line.qte += self.qte
            duplicated_line.save()
        else:
            self.save()

    def get_absolute_url(self):
        return reverse('commande_details', args=[self.commande.pk])
