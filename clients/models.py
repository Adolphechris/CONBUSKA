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


class PaiementClient(models.Model):
    client = models.ForeignKey(Client, on_delete=models.PROTECT, null=False)
    montant = models.DecimalField(max_digits=8, decimal_places=4)
    date_paiement = models.DateField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey('users.CustomUser',
                                 related_name='paiementclientcreepar',
                                 on_delete=models.PROTECT)
    modifie_par = models.ForeignKey('users.CustomUser',
                                    blank=True, null=True,
                                    related_name='paiementclientmodpar',
                                    on_delete=models.PROTECT)
    objects = models.Manager()