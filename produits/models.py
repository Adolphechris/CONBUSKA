from django.db import models
from django.urls import reverse
from django.forms.models import model_to_dict
from parametres.models import Magasin
from common.utils import is_duplicate
from django.templatetags.static import static


class Categorie(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom

    @staticmethod
    def get_absolute_url():
        return reverse('categories')


class Unite(models.Model):
    nom = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom

    @staticmethod
    def get_absolute_url():
        return reverse('unites')


class Article(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    code = models.IntegerField(unique=True, blank=False)
    designation = models.CharField(max_length=250, unique=True)
    description = models.TextField()
    # code_barre = models.CharField(max_length=35)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT)
    unite = models.ForeignKey(Unite, on_delete=models.PROTECT)
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.PROTECT, null=True)
    prix_achat = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    prix_vente = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    prix_vente_gros = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=2, choices=DEVISES)
    seuil = models.IntegerField()
    seuil_gros = models.IntegerField()
    emplacement = models.CharField(max_length=150)
    photo1 = models.ImageField(upload_to='articles/', blank=True)
    photo2 = models.ImageField(upload_to='articles/', blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)

    objects = models.Manager()

    def __str__(self):
        return f'{self.designation} | {self.stock} | {self.prix_vente}FC | {self.prix_vente_gros}FC'

    @property
    def stock(self):
        get_stock = Stock.objects.filter(article=self.pk)
        stock = sum(i.qte for i in get_stock)
        return stock

    @property
    def prix_vente_devise(self):
        if self.devise == '$':
            prix_vente_fc = self.prix_vente * 2800
            prix_vente_usd = self.prix_vente
        else:
            prix_vente_usd = round(self.prix_vente / 2800, 2)
            prix_vente_fc = self.prix_vente
        return prix_vente_fc, prix_vente_usd

    @property
    def prix_vente_gros_devise(self):
        if self.devise == '$':
            prix_vente_gros_fc = self.prix_vente_gros * 2800
            prix_vente_gros_usd = self.prix_vente_gros
        else:
            prix_vente_gros_usd = round(self.prix_vente_gros / 2800, 2)
            prix_vente_gros_fc = self.prix_vente_gros
        return prix_vente_gros_fc, prix_vente_gros_usd

    @property
    def get_next_code(self):
        last_code = Article.objects.all().order_by('-code')[:1]
        try:
            code = [i.code + 1 for i in last_code][0]
        except IndexError:
            code = 1000
        return code

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code

        super(Article, self).save(*args, **kwargs)

    def photo1_url(self):
        if self.photo1:
            return self.photo1.url
        return static('img/default-article.png')

    def photo2_url(self):
        if self.photo2:
            return self.photo2.url
        return static('img/default-article.png')

    def get_absolute_url(self):
        return reverse('article_details', args=[self.pk])


class Stock(models.Model):
    magasin = models.ForeignKey(Magasin, on_delete=models.PROTECT)
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    qte = models.IntegerField(blank=False, null=False, default=0)
    date_peremption = models.DateField(blank=False, null=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    def __str__(self):
        return self.article
