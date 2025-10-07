from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from caisse.models import Caisse


class TypeProfile(models.Model):
    nom = models.CharField(max_length=20)
    description = models.TextField()

    def __str__(self):
        return self.nom


class CustomUser(AbstractUser):
    telephone = models.CharField(max_length=12, blank=True, null=True)
    photo = models.ImageField(upload_to='photos_users/', blank=True)
    type_profile = models.ForeignKey(TypeProfile, related_name='profiles', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('user_details', args=[str(self.pk)])


class Caissier(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='medecin')
    caisse = models.ForeignKey(Caisse, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.username} - {self.caisse.nom}'