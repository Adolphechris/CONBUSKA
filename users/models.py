from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from caisse.models import Caisse


class TypeProfile(models.Model):
    nom = models.CharField(max_length=50)
    slug = models.CharField(max_length=30, unique=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom


class CustomUser(AbstractUser):
    telephone = models.CharField(max_length=12, blank=True, null=True)
    photo = models.ImageField(upload_to='photos_users/', blank=True)
    type_profile = models.ForeignKey(TypeProfile, related_name='profiles', on_delete=models.PROTECT, null=True)
    force_password_change = models.BooleanField(default=True)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('user_details', args=[str(self.pk)])

    @property
    def role_slug(self):
        if self.type_profile:
            return self.type_profile.slug
        return None


class Caissier(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='caissier')
    caisse = models.ForeignKey(Caisse, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.username} - {self.caisse.nom}'