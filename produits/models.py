from django.db import models
from django.urls import reverse
from django.forms.models import model_to_dict
# from common.utils import is_duplicate


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


class Article(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    code = models.IntegerField(unique=True, blank=False)
    designation = models.CharField(max_length=250, unique=True)
    description = models.TextField()
    code_barre = models.CharField(max_length=35)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT)
    unite = models.ForeignKey(Unite, on_delete=models.PROTECT)
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.PROTECT, null=True)
    prix_achat = models.DecimalField(default=0.0, max_digits=8, decimal_places=4)
    prix_vente = models.DecimalField(default=0.0, max_digits=8, decimal_places=4)
    prix_vente_gros = models.DecimalField(default=0.0, max_digits=8, decimal_places=4)
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
        return self.designation

    @property
    def get_next_code(self):
        last_code = Article.objects.all().order_by('-code')[:1]
        try:
            code = [i.code + 1 for i in last_code][0]
        except IndexError:
            code = 1000
        return code

    @staticmethod
    def get_absolute_url():
        return reverse('articles')


class Stock(models.Model):
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    qte = models.IntegerField(blank=False, null=False)
    date_peremption = models.DateField(blank=False, null=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    def __str__(self):
        return self.article

    def valid(self):
        data = {'article': self.article.id, 'lot': self.lot}
        items = Stock.objects.filter(produit=data.get('produit'))
        items_to_dict = [model_to_dict(i) for i in items]

        duplicate = True # is_duplicate(items_to_dict, data)
        if duplicate:
            duplicated_line = Stock.objects.get(id=duplicate['id'])
            # delta = abs(duplicated_line.qte - self.qte)
            duplicated_line.qte += self.qte
            duplicated_line.save()
        else:
            self.save()

    def remove(self, qte):
        if self.qte - qte != 0:
            self.qte -= qte
            self.save()
        else:
            self.delete()
