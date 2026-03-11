import decimal
from django.db import models, transaction
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.db.models import Max, Count, Sum, F, DecimalField
from django.db.models.functions import TruncDate
from django.utils import timezone
import datetime


class Livreur(models.Model):
    nom = models.CharField(max_length=30)
    livraison = models.IntegerField(default=0)
    def __str__(self):
        return self.nom


class FactureManager(models.Manager):
    def ventes_journalieres(self, date_debut=None, date_fin=None):
        today = timezone.now().date()
        if date_debut is None:
            date_debut = today
        if date_fin is None:
            date_fin = today
        return (self.get_queryset()
                .filter(date_facture__range=(date_debut, date_fin))
                .annotate(date=TruncDate('date_facture'))
                .values('date')
                .annotate(
                    nb_factures=Count('id', distinct=True),
                    total_vendu=Sum(
                        F('facture_details__qte') * F('facture_details__prix'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ) - Sum('remise', distinct=True)
                )
                .order_by('date'))


class Facture(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    numero = models.IntegerField(unique=True, blank=False)
    date_facture = models.DateField(default=datetime.date.today)
    devise = models.CharField(max_length=2, choices=DEVISES)
    taux = models.DecimalField(default=0.0, max_digits=6, decimal_places=2)
    remise = models.DecimalField(default=0, max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
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
    valide = models.BooleanField(default=False)

    objects = FactureManager()

    def __str__(self):
        return str(self.numero)

    @property
    def sous_total(self):
        result = DetailsFacture.objects.filter(facture=self) \
            .annotate(sub=F("qte") * F("prix")) \
            .aggregate(total=Sum("sub"))["total"]

        return result or decimal.Decimal(0)

    @property
    def total(self):
        return self.sous_total - self.remise

    @property
    def total_devise(self):
        return self.total / self.taux

    @property
    def total_articles(self):
        return DetailsFacture.objects.filter(facture=self.pk).count()

    @classmethod
    def get_next_num(cls):
        with transaction.atomic():
            last_num = cls.objects.select_for_update().aggregate(Max("numero"))["numero__max"]
        if last_num:
            return last_num + 1
        return int(timezone.now().strftime("%y") + "0000")

    def save(self, *args, **kwargs):
        if self.numero is None:
            self.numero = self.get_next_num()

        super(Facture, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('facture_details', args=[self.pk])


class DetailsFacture(models.Model):
    facture = models.ForeignKey(Facture, related_name='facture_details', on_delete=models.PROTECT, null=True)
    article = models.ForeignKey('produits.Article', on_delete=models.PROTECT, null=True)
    qte = models.IntegerField()
    prix = models.DecimalField(max_digits=12, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    @property
    def total(self):
        return self.qte * self.prix


class FactureClient(models.Model):
    facture = models.OneToOneField(Facture, related_name='facture_client', on_delete=models.PROTECT)
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT)
