from django.db import models, transaction
from django.urls import reverse
from produits.models import Stock, Magasin
from django.db.models import Max
from django.utils.timezone import now
import datetime


class Livreur(models.Model):
    nom = models.CharField(max_length=30)
    livraison = models.IntegerField(default=0)
    def __str__(self):
        return self.nom


class Facture(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    numero = models.IntegerField(unique=True, blank=False)
    date_facture = models.DateField(default=datetime.date.today)
    devise = models.CharField(max_length=2, choices=DEVISES)
    taux = models.DecimalField(default=0.0, max_digits=6, decimal_places=2)
    remise = models.DecimalField(default=0.0, max_digits=6, decimal_places=2)
    client_comptoir = models.CharField(max_length=30, null=True, blank=True)
    livreur = models.ForeignKey(Livreur, on_delete=models.PROTECT, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey('users.CustomUser',
                                 related_name='facturecreepar',
                                 on_delete=models.PROTECT)
    modifie_par = models.ForeignKey('users.CustomUser',
                                    blank=True, null=True,
                                    related_name='facturemodpar',
                                    on_delete=models.PROTECT)
    actif = models.BooleanField(default=True)

    objects = models.Manager()

    def __str__(self):
        return self.numero

    @property
    def sous_total(self):
        get_details = DetailsFacture.objects.filter(facture=self.pk)
        resultat = sum(i.qte * i.prix for i in get_details)
        return resultat

    @property
    def total(self):
        return self.sous_total - self.remise

    @property
    def total_devise(self):
        return self.total / self.taux

    @classmethod
    def get_next_num(cls):
        last_num = cls.objects.aggregate(Max('numero'))['numero__max']
        if last_num:
            return last_num + 1
        # Format de départ basé sur l’année : exemple 250000
        return int(now().strftime('%y') + '0000')

    def save(self, *args, **kwargs):
        if self.numero is None:
            self.numero = self.get_next_num()

        super(Facture, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('facture_details', args=[self.pk])


class DetailsFacture(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.PROTECT, null=True)
    article = models.ForeignKey('produits.Article', on_delete=models.PROTECT, null=True)
    qte = models.IntegerField()
    prix = models.DecimalField(max_digits=8, decimal_places=4)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    @property
    def total(self):
        return self.qte * self.prix

    @transaction.atomic
    def add(self):
        detail, created = DetailsFacture.objects.get_or_create(
            facture=self.facture,
            article=self.article,
            defaults={
                'qte': self.qte,
                'prix': self.article.prix_vente,
            }
        )

        if not created:
            detail.qte += self.qte
            detail.save()

        magasin = Magasin.objects.get(nom="Alimentation")
        all_stock = Stock.objects.select_for_update().filter(magasin=magasin.pk,
                                                             article=self.article).order_by('date_peremption')

        qte = self.qte
        print("STEP 1. NEW QTE = ", qte)
        for stock in all_stock:
            if qte > 0:
                if stock.qte >= qte:
                    stock.qte -= qte
                    stock.save()
                    delta = qte
                    qte = 0
                else:
                    print("STEP 2. STOCK QTE = ", stock.qte)
                    delta = stock.qte
                    qte -= stock.qte
                    stock.qte = 0
                    stock.save()

                    print("STEP 3. DELTA = ", delta)

                # Enregistrement de la reference dans DetailsLigneFacture
                detail_ligne, created_ligne = DetailsLigneFacture.objects.get_or_create(
                    detail_facture=detail,
                    date_peremption=stock.date_peremption,
                    defaults={
                        'qte': delta,
                    }
                )

                if not created_ligne:
                    print("STEP 4. QTE TO SAVE = ", delta)
                    detail_ligne.qte += delta
                    detail_ligne.save()


                if stock.qte <= 0:
                    stock.delete()
            else:
                break

    @transaction.atomic
    def update_facture(self):
        old_details = DetailsFacture.objects.get(pk=self.pk)
        old_article = old_details.article
        old_qte = old_details.qte

        # Valeurs modifiées
        new_article = self.article
        new_qte = self.qte

        facture = self.facture
        magasin = Magasin.objects.get(nom="Alimentation")

        # Même article ➜ simple update
        if old_article == new_article:
            delta = old_qte - new_qte

            # CAS 1 le delta est superieur à 0 -> Diminution de la quantite initiale
            if delta > 0:
                self.save()

                get_lignes_facture = DetailsLigneFacture.objects.filter(detail_facture=old_details.pk).order_by("-date_peremption")
                for i in get_lignes_facture:
                    if delta >= i.qte:
                        delta -= i.qte
                        qte = i.qte
                    else:
                        qte = delta
                        delta = 0

                    i.qte -= qte
                    if i.qte <= 0:
                        i.delete()
                    else:
                        i.save()

                    # Mise à jour du stock
                    stock, stock_created = Stock.objects.get_or_create(
                        magasin=magasin,
                        article=old_article,
                        date_peremption=i.date_peremption,
                        defaults={'qte': qte}
                    )

                    if not stock_created:
                        stock.qte += qte
                        stock.save()
            else:
                self.qte = new_qte - old_qte
                self.add()

        else:
            # Fusion avec ligne existante si elle existe
            autre_detail = DetailsFacture.objects.filter(
                facture=facture,
                article=new_article,
            ).exclude(pk=self.pk).first()

            if autre_detail:
                autre_detail.qte += new_qte
                autre_detail.save()
                self.delete()
            else:
                self.save()

    @transaction.atomic
    def delte_facture(self):
        magasin = Magasin.objects.get(nom="Alimentation")
        get_lignes_facture = DetailsLigneFacture.objects.filter(detail_facture=self.pk)
        for i in get_lignes_facture:
            stock, stock_created = Stock.objects.get_or_create(
                magasin=magasin,
                article=i.article,
                date_peremption=i.date_peremption,
                defaults={'qte': i.qte}
            )

            if not stock_created:
                stock.qte += i.qte
                stock.save()

            i.delete()
        self.delete()


class DetailsLigneFacture(models.Model):
    detail_facture = models.ForeignKey(DetailsFacture, on_delete=models.PROTECT, null=True)
    qte = models.IntegerField()
    date_peremption = models.DateField(blank=False, null=False)
    date_creation = models.DateTimeField(auto_now_add=True)