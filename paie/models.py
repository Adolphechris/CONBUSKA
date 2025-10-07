from django.db import models
from django.urls import reverse
from django.db.models import Max


class Agent(models.Model):
    matricule = models.IntegerField(unique=True, blank=False)
    photo = models.ImageField(upload_to='agents/', blank=True)
    nom = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    adresse = models.CharField(max_length=150)
    telephone = models.CharField(max_length=150)
    ville = models.CharField(max_length=30)
    salaire = models.DecimalField(max_digits=8, decimal_places=4)

    objects = models.Manager()

    def __str__(self):
        return self.nom

    @classmethod
    def get_next_matricule(cls):
        last_matricule = cls.objects.aggregate(Max('matricule'))['matricule__max']
        if last_matricule:
            return last_matricule + 1
        return 4000

    def save(self, *args, **kwargs):
        if self.matricule is None:
            self.matricule = self.get_next_matricule()

        super(Agent, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('agent_details', args=[self.pk])


class Paie(models.Model):
    mois = models.DateField(blank=False, null=False)
    cree_par = models.ForeignKey('users.CustomUser',
                                 related_name='paiecreepar',
                                 on_delete=models.PROTECT)
    modifie_par = models.ForeignKey('users.CustomUser',
                                    blank=True, null=True,
                                    related_name='paiemodpar',
                                    on_delete=models.PROTECT)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide = models.BooleanField(default=False)
    objects = models.Manager()


class DetailsPaie(models.Model):
    paie = models.ForeignKey(Paie, related_name='details_paie', on_delete=models.PROTECT)
    agent = models.ForeignKey(Agent, related_name='agent_paie_details', on_delete=models.PROTECT)
    salaire = models.DecimalField(max_digits=8, decimal_places=4)
    montant_percu = models.DecimalField(max_digits=8, decimal_places=4)
    jap = models.IntegerField(default=26)
    jp = models.IntegerField(default=26)
    absence = models.IntegerField(default=0)
