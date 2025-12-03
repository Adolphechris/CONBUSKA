from django.db import models
from django.urls import reverse
from django.db import transaction
from produits.models import Stock
from django.db.models import Max
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
    def cout_achat(self):
        details_approvisionnement = DetailsApprovisionnement.objects.filter(approvisionnement=self.pk)
        total = sum(i.cout_achat for i in details_approvisionnement)
        return total

    @classmethod
    def get_next_num(cls):
        with transaction.atomic():
            last = cls.objects.select_for_update().aggregate(Max("numero"))["numero__max"]
            return (last + 1) if last else int(datetime.datetime.now().strftime('%y') + '0000')

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero:
            self.numero = self.get_next_num()

        super(Approvisionnement, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('approvisionnement_details', args=[self.pk])


class DetailsApprovisionnement(models.Model):
    approvisionnement = models.ForeignKey(Approvisionnement, on_delete=models.PROTECT, null=True)
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.PROTECT, null=False)
    facture = models.CharField(max_length=15)
    transport = models.DecimalField(max_digits=8, decimal_places=4)
    chargement = models.DecimalField(max_digits=8, decimal_places=4)
    dechargement = models.DecimalField(max_digits=8, decimal_places=4)
    services = models.DecimalField(max_digits=8, decimal_places=4)
    entreposage = models.DecimalField(max_digits=8, decimal_places=4)
    declaration = models.DecimalField(max_digits=8, decimal_places=4)
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
        total = (self.declaration + self.transport + self.chargement + self.dechargement + self.services +
                 self.entreposage + self.autre_frais)
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
    def add(self):
        detail, created = DetailsApprovisionnement.objects.get_or_create(
            approvisionnement=self.approvisionnement,
            article=self.article,
            date_peremption=self.date_peremption,
            fournisseur=self.fournisseur,
            facture=self.facture,
            defaults={
                'declaration': self.declaration,
                'transport': self.transport,
                'chargement': self.chargement,
                'dechargement': self.dechargement,
                'services': self.services,
                'entreposage': self.entreposage,
                'autre_frais': self.autre_frais,
                'qte': self.qte,
                'prix': self.prix,
            }
        )

        if not created:
            detail.qte += self.qte
            detail.save()

        # Mise à jour ou création du stock
        stock, stock_created = Stock.objects.get_or_create(
            magasin=self.approvisionnement.magasin,
            article=self.article,
            date_peremption=self.date_peremption,
            defaults={'qte': self.qte}
        )
        if not stock_created:
            stock.qte += self.qte
            stock.save()

    @transaction.atomic
    def update_appro(self):
        old_details = DetailsApprovisionnement.objects.get(pk=self.pk)
        print(old_details)
        old_article = old_details.article
        old_peremption = old_details.date_peremption
        old_qte = old_details.qte

        # Valeurs modifiées
        new_article = self.article
        new_peremption = self.date_peremption
        new_qte = self.qte

        appro = self.approvisionnement

        # Même article / même date ➜ simple update
        if (old_article == new_article) and (old_peremption == new_peremption):
            self.save()

            stock = Stock.objects.get(
                magasin=appro.magasin.pk,
                article=old_article,
                date_peremption=old_peremption
            )
            stock.qte = stock.qte - old_qte + new_qte
            stock.save()

        else:
            # Fusion avec ligne existante si elle existe
            autre_detail = DetailsApprovisionnement.objects.filter(
                approvisionnement=appro,
                article=new_article,
                date_peremption=new_peremption
            ).exclude(pk=self.pk).first()

            if autre_detail:
                autre_detail.qte += new_qte
                autre_detail.save()
                self.delete()
            else:
                self.save()

            # Mise à jour du stock
            # Ancienne ligne
            stock_old = Stock.objects.get(
                magasin=appro.magasin,
                article=old_article,
                date_peremption=old_peremption
            )
            stock_old.qte -= old_qte
            if stock_old.qte <= 0:
                stock_old.delete()
            else:
                stock_old.save()

            # Nouvelle ligne
            stock_new, created = Stock.objects.get_or_create(
                magasin=appro.magasin,
                article=new_article,
                date_peremption=new_peremption,
                defaults={'qte': new_qte}
            )
            if not created:
                stock_new.qte += new_qte
                stock_new.save()


    def save(self, *args, **kwargs):

        super(DetailsApprovisionnement, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('approvisionnement_details', args=[self.approvisionnement.pk])
