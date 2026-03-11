from django.db import models
from django.urls import reverse
from django.db import transaction
from django.db.models import Max, Sum
import datetime


class TypeFrais(models.Model):
    nom = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="fa-money")
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.nom


class Approvisionnement(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    numero = models.IntegerField(unique=True, blank=False)
    magasin = models.ForeignKey('parametres.Magasin', on_delete=models.PROTECT, null=False)
    devise = models.CharField(max_length=2, choices=DEVISES)
    taux = models.DecimalField(default=0.0, max_digits=6, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey('users.CustomUser',
                                 related_name='approvisionnementcreepar',
                                 on_delete=models.PROTECT)
    modifie_par = models.ForeignKey('users.CustomUser',
                                    blank=True, null=True,
                                    related_name='approvisionnementmodpar',
                                    on_delete=models.PROTECT)
    actif = models.BooleanField(default=True)
    valide = models.BooleanField(default=False)
    objects = models.Manager()

    def __str__(self):
        return str(self.numero)

    @property
    def total_approvisionnement(self):
        return sum(i.prix_total for i in self.detailsapprovisionnement_set.all())

    @property
    def frais_achat_total(self):
        return sum(i.frais_achat * i.qte for i in self.detailsapprovisionnement_set.all())

    @property
    def cout_achat(self):
        return sum(i.cout_achat * i.qte for i in self.detailsapprovisionnement_set.all())

    @property
    def resultat_total(self):
        return sum(i.resultat for i in self.detailsapprovisionnement_set.all())

    @property
    def chiffre_affaires(self):
        return sum(i.prix_vente * i.qte for i in self.detailsapprovisionnement_set.all())

    @classmethod
    def get_next_num(cls):
        with transaction.atomic():
            last = cls.objects.select_for_update().aggregate(Max("numero"))["numero__max"]
            return (last + 1) if last else int(datetime.datetime.now().strftime('%y') + '0000')

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero:
            self.numero = self.get_next_num()

        super(Approvisionnement, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('approvisionnement_details', args=[self.pk])


class DetailsApprovisionnement(models.Model):
    approvisionnement = models.ForeignKey(Approvisionnement, on_delete=models.PROTECT, null=True)
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.PROTECT, null=False)
    facture = models.CharField(max_length=15)
    article = models.ForeignKey('produits.Article', on_delete=models.PROTECT, null=True)
    qte = models.IntegerField()
    prix = models.DecimalField(max_digits=12, decimal_places=2)
    date_peremption = models.DateField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    @property
    def prix_total(self):
        return self.qte * self.prix

    @property
    def frais_achat(self):
        return self.frais.aggregate(
            total=Sum("montant")
        )["total"] or 0

    @property
    def cout_achat(self):
        return self.prix + self.frais_achat

    @property
    def prix_vente(self):
        prix_vente_fc, prix_vente_usd = self.article.prix_vente_devise
        if self.approvisionnement.devise == '$':
            return prix_vente_usd
        else:
            return prix_vente_fc

    @property
    def prix_vente_gros(self):
        prix_vente_gros_fc, prix_vente_gros_usd = self.article.prix_vente_gros_devise
        if self.approvisionnement.devise == '$':
            return prix_vente_gros_usd
        else:
            return prix_vente_gros_fc

    @property
    def resultat(self):
        prix_vente_fc, prix_vente_usd = self.article.prix_vente_devise
        if self.approvisionnement.devise == '$':
            return (prix_vente_usd - self.cout_achat) * self.qte
        else:
            return (prix_vente_fc - self.cout_achat) * self.qte

    @transaction.atomic
    def add(self):
        detail, created = DetailsApprovisionnement.objects.get_or_create(
            approvisionnement=self.approvisionnement,
            article=self.article,
            date_peremption=self.date_peremption,
            fournisseur=self.fournisseur,
            facture=self.facture,
            defaults={
                'qte': self.qte,
                'prix': self.prix,
            }
        )

        if not created:
            detail.qte += self.qte
            detail.save()

        return detail

    @transaction.atomic
    def update_appro(self):
        old_details = DetailsApprovisionnement.objects.get(pk=self.pk)
        old_peremption = old_details.date_peremption

        # Article et fournisseur sont verrouillés — on les réaffecte
        # depuis la BDD pour ignorer toute valeur injectée via POST.
        self.article = old_details.article
        self.fournisseur = old_details.fournisseur

        new_peremption = self.date_peremption
        new_qte = self.qte
        appro = self.approvisionnement

        # Même date de péremption ➜ simple update (article/fournisseur déjà verrouillés)
        if old_peremption == new_peremption:
            self.save()
        else:
            # Fusion uniquement avec une ligne de même source
            # (article + fournisseur + facture + nouvelle date de péremption).
            # Sans fournisseur/facture dans le filtre, on risquait de fusionner
            # deux lignes de sources différentes → perte de traçabilité.
            autre_detail = DetailsApprovisionnement.objects.filter(
                approvisionnement=appro,
                article=self.article,
                fournisseur=self.fournisseur,
                facture=self.facture,
                date_peremption=new_peremption,
            ).exclude(pk=self.pk).first()

            if autre_detail:
                autre_detail.qte += new_qte
                autre_detail.save()
                self.delete()
            else:
                self.save()


    def save(self, *args, **kwargs):

        super(DetailsApprovisionnement, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('approvisionnement_details', args=[self.approvisionnement.pk])


class FraisApprovisionnement(models.Model):
    detail = models.ForeignKey(DetailsApprovisionnement, related_name="frais", on_delete=models.CASCADE)
    type_frais = models.ForeignKey(TypeFrais, on_delete=models.PROTECT)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
