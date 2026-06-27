from django.db import models
from django.urls import reverse
from django.db.models import Max, Sum
from django.db import transaction
from caisse.models import MouvementCaisseCreancier, MouvementCaisseDebiteur


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

    def prets(self):
        return (
            MouvementCaisseCreancier.objects
            .select_related("mouvement_caisse")
            .filter(creancier=self, mouvement_caisse__type_mouvement="ENTREE")
        )

    def paiements(self):
        return (
            MouvementCaisseCreancier.objects
            .select_related("mouvement_caisse")
            .filter(creancier=self, mouvement_caisse__type_mouvement="SORTIE")
        )

    def total_prets_usd(self):
        from decimal import Decimal
        return self.prets().aggregate(total=Sum('valeur_usd'))['total'] or Decimal('0')

    def total_paiements_usd(self):
        from decimal import Decimal
        return self.paiements().aggregate(total=Sum('valeur_usd'))['total'] or Decimal('0')

    def solde_usd(self):
        return self.total_prets_usd() - self.total_paiements_usd()

    def solde_fc(self):
        return self.total_prets() - self.total_paiements()

    def total_prets(self):
        return self.prets().aggregate(total=Sum('mouvement_caisse__montant'))['total'] or 0

    def total_paiements(self):
        return self.paiements().aggregate(total=Sum('mouvement_caisse__montant'))['total'] or 0

    def solde(self):
        return self.solde_usd()

    @classmethod
    def get_next_code(cls):
        with transaction.atomic():
            last = cls.objects.select_for_update().aggregate(Max("code"))["code__max"]
            return (last + 1) if last else 4000

    def save(self, *args, **kwargs):
        if not self.pk and not self.code:
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

    def prets(self):
        return (
            MouvementCaisseDebiteur.objects
            .select_related("mouvement_caisse")
            .filter(debiteur=self, mouvement_caisse__type_mouvement="SORTIE")
        )

    def paiements(self):
        return (
            MouvementCaisseDebiteur.objects
            .select_related("mouvement_caisse")
            .filter(debiteur=self, mouvement_caisse__type_mouvement="ENTREE")
        )

    def total_prets_usd(self):
        from decimal import Decimal
        return self.prets().aggregate(total=Sum('valeur_usd'))['total'] or Decimal('0')

    def total_paiements_usd(self):
        from decimal import Decimal
        return self.paiements().aggregate(total=Sum('valeur_usd'))['total'] or Decimal('0')

    def solde_usd(self):
        return self.total_prets_usd() - self.total_paiements_usd()

    def solde_fc(self):
        return self.total_prets() - self.total_paiements()

    def total_prets(self):
        return self.prets().aggregate(total=Sum('mouvement_caisse__montant'))['total'] or 0

    def total_paiements(self):
        return self.paiements().aggregate(total=Sum('mouvement_caisse__montant'))['total'] or 0

    def solde(self):
        return self.solde_usd()

    def __str__(self):
        return self.nom

    @classmethod
    def get_next_code(cls):
        with transaction.atomic():
            last = cls.objects.select_for_update().aggregate(Max("code"))["code__max"]
            return (last + 1) if last else 5000

    def save(self, *args, **kwargs):
        if not self.pk and not self.code:
            self.code = self.get_next_code()

        super(Debiteur, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('debiteur_details', args=[self.pk])