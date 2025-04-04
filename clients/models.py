from django.db import models
from django.urls import reverse


class Client(models.Model):
    code = models.IntegerField(unique=True, blank=False)
    photo = models.ImageField(upload_to='clients/', blank=True)
    nom = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    adresse = models.CharField(max_length=150)
    telephone = models.CharField(max_length=150)
    ville = models.CharField(max_length=30)

    objects = models.Manager()

    def __str__(self):
        return self.nom

    @property
    def get_next_code(self):
        last_code = Client.objects.all().order_by('-code')[:1]
        try:
            code = [i.code + 1 for i in last_code][0]
        except IndexError:
            code = 3000
        return code

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code

        super(Client, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('client_details', args=[self.pk])

