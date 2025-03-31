from django.db import models
from django.urls import reverse


class Parametre(models.Model):
    code = models.CharField(max_length=6, default='Params')
    logo = models.ImageField(upload_to='logo/', blank=True, null=True)
    sigle = models.CharField(max_length=30, blank=True, null=True)
    societe = models.CharField(max_length=40, blank=True, null=True)
    rccm = models.CharField(max_length=40, blank=True, null=True)
    idnat = models.CharField(max_length=40, blank=True, null=True)
    impot = models.CharField(max_length=40, blank=True, null=True)
    tva = models.CharField(max_length=50, blank=True, null=True)
    pays = models.CharField(max_length=30, blank=True, null=True)
    adresse = models.CharField(max_length=150, blank=True, null=True)
    ville = models.CharField(max_length=30, blank=True, null=True)
    telephone = models.CharField(max_length=40, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def __str__(self):
        return self.code

    @staticmethod
    def get_absolute_url():
        return reverse('parametres')


class Magasin(models.Model):
    nom = models.CharField(max_length=25)
    description = models.TextField()
    is_principal = models.BooleanField(default=False)
    localisation = models.CharField(max_length=30)

    @staticmethod
    def get_absolute_url():
        return reverse('magasins')
