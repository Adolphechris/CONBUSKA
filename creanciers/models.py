from django.db import models
from django.urls import reverse
from django.db.models import Max


class Creancier(models.Model):
    code = models.IntegerField(unique=True, blank=False)
    photo = models.ImageField(upload_to='creanciers/', blank=True)
    nom = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    adresse = models.CharField(max_length=150)
    telephone = models.CharField(max_length=150)
    ville = models.CharField(max_length=30)

    objects = models.Manager()

    def __str__(self):
        return self.nom

    @classmethod
    def get_next_code(cls):
        last_code = cls.objects.aggregate(Max('code'))['code__max']
        if last_code:
            return last_code + 1
        return 4000

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code()

        super(Creancier, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('creancier_details', args=[self.pk])


class Debiteur(models.Model):
    code = models.IntegerField(unique=True, blank=False)
    photo = models.ImageField(upload_to='debiteurs/', blank=True)
    nom = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    adresse = models.CharField(max_length=150)
    telephone = models.CharField(max_length=150)
    ville = models.CharField(max_length=30)

    objects = models.Manager()

    def __str__(self):
        return self.nom

    @classmethod
    def get_next_code(cls):
        last_code = cls.objects.aggregate(Max('code'))['code__max']
        if last_code:
            return last_code + 1
        return 5000

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code()

        super(Debiteur, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('debiteur_details', args=[self.pk])