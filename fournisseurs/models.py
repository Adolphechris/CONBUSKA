from django.db import models
from django.urls import reverse


class Fournisseur(models.Model):
    code = models.IntegerField(unique=True, blank=False)
    photo = models.ImageField(upload_to='fournisseurs/', blank=True)
    nom = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    adresse = models.CharField(max_length=150)
    telephone = models.CharField(max_length=150)
    ville = models.CharField(max_length=30)
    pays = models.CharField(max_length=30)
    tuteur = models.CharField(max_length=30)
    rccm = models.CharField(max_length=30)
    id_nat = models.CharField(max_length=30)
    impot = models.CharField(max_length=30)
    tva = models.CharField(max_length=30)

    objects = models.Manager()

    def __str__(self):
        return self.nom

    @property
    def get_next_code(self):
        last_code = Fournisseur.objects.all().order_by('-code')[:1]
        try:
            code = [i.code + 1 for i in last_code][0]
        except IndexError:
            code = 2000
        return code

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code

        super(Fournisseur, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('fournisseur_details', args=[self.pk])
