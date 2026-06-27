from django.db import models
from django.db.models import Max, Q, Value
from django.db.models.aggregates import Sum, Coalesce
from django.urls import reverse
from django.forms.models import model_to_dict
from parametres.models import Magasin
from django.templatetags.static import static
from django.db import transaction
import datetime


class Categorie(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom

    @staticmethod
    def get_absolute_url():
        return reverse('categories')


class Unite(models.Model):
    nom = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom

    @staticmethod
    def get_absolute_url():
        return reverse('unites')


class ArticleQuerySet(models.QuerySet):
    def with_stock(self):
        main_id = Magasin.objects.filter(is_principal=True).values_list('id', flat=True).first()
        return self.annotate(
            stock_dispo=Coalesce(
                Sum(
                    'stock__qte',
                    filter=Q(stock__magasin_id=main_id)
                ),
                Value(0)
            )
        )

    def available(self):
        return self.with_stock().filter(stock_dispo__gt=0)


class ArticleManager(models.Manager):
    def get_queryset(self):
        return ArticleQuerySet(self.model, using=self._db)

    def with_stock(self):
        return self.get_queryset().with_stock()


class Article(models.Model):
    DEVISES = (
        ('$', '$'),
        ('FC', 'FC'),
    )
    code = models.IntegerField(unique=True, blank=False)
    designation = models.CharField(max_length=250, unique=True)
    description = models.TextField()
    # code_barre = models.CharField(max_length=35)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT)
    unite = models.ForeignKey(Unite, on_delete=models.PROTECT)
    fournisseur = models.ForeignKey('fournisseurs.Fournisseur', on_delete=models.PROTECT, null=True)
    prix_achat = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    prix_vente = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    prix_vente_gros = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=2, choices=DEVISES)
    seuil = models.IntegerField()
    seuil_gros = models.IntegerField()
    emplacement = models.CharField(max_length=150)
    photo1 = models.ImageField(upload_to='articles/', blank=True)
    photo2 = models.ImageField(upload_to='articles/', blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    # ── Nouveaux champs e-commerce (Sprint 1) ────────────────────────
    est_publie = models.BooleanField(
        default=False,
        verbose_name="Publié en ligne",
        help_text="Si True, l'article apparaît sur la boutique en ligne"
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        null=True,
        help_text="URL SEO générée automatiquement depuis le nom"
    )
    derniere_sync_firestore = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière synchronisation Firestore",
        help_text="Timestamp de la dernière sync réussie vers Firestore"
    )

    objects = ArticleManager()

    def __str__(self):
        return self.designation

    @property
    def stock(self):
        default_magasin = Magasin.objects.only("id").filter(is_principal=True).first()

        if not default_magasin:
            return 0

        return (
            Stock.objects
            .filter(article=self, magasin=default_magasin)
            .aggregate(total=Sum("qte"))["total"] or 0
        )

    def _get_taux(self):
        from parametres.models import get_taux_usd_cdf
        return get_taux_usd_cdf()

    @property
    def prix_vente_devise(self):
        taux = self._get_taux()
        if self.devise == '$':
            prix_vente_fc = self.prix_vente * taux
            prix_vente_usd = self.prix_vente
        else:
            prix_vente_usd = round(self.prix_vente / taux, 2)
            prix_vente_fc = self.prix_vente
        return prix_vente_fc, prix_vente_usd

    @property
    def prix_vente_gros_devise(self):
        taux = self._get_taux()
        if self.devise == '$':
            prix_vente_gros_fc = self.prix_vente_gros * taux
            prix_vente_gros_usd = self.prix_vente_gros
        else:
            prix_vente_gros_usd = round(self.prix_vente_gros / taux, 2)
            prix_vente_gros_fc = self.prix_vente_gros
        return prix_vente_gros_fc, prix_vente_gros_usd

    @classmethod
    def get_next_code(cls):
        with transaction.atomic():
            last = cls.objects.select_for_update().aggregate(Max("code"))["code__max"]
            return (last + 1) if last else 1000

    def save(self, *args, **kwargs):
        if self.code is None:
            self.code = self.get_next_code()

        super(Article, self).save(*args, **kwargs)

    def photo1_url(self):
        if self.photo1:
            return self.photo1.url
        return static('img/default-article.png')

    def photo2_url(self):
        if self.photo2:
            return self.photo2.url
        return static('img/default-article.png')

    def get_absolute_url(self):
        return reverse('article_details', args=[self.pk])


class Stock(models.Model):
    magasin = models.ForeignKey(Magasin, on_delete=models.PROTECT)
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    qte = models.IntegerField(blank=False, null=False, default=0)
    date_peremption = models.DateField(blank=False, null=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    def __str__(self):
        return str(self.article)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["magasin", "article", "date_peremption"],
                name="unique_lot_stock"
            ),
            models.CheckConstraint(
                check=models.Q(qte__gte=0),
                name="stock_non_negatif"
            ),
        ]


class MouvementStock(models.Model):
    IN = "IN"
    OUT = "OUT"

    TYPE_CHOICES = [
        (IN, "Entrée"),
        (OUT, "Sortie"),
    ]

    magasin = models.ForeignKey(Magasin, on_delete=models.PROTECT)
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    qte = models.PositiveIntegerField()
    date_peremption = models.DateField(null=True, blank=True)

    source_type = models.CharField(max_length=50)
    source_id = models.PositiveIntegerField()

    annule_mouvement = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                                         related_name='compensatoires')

    date_creation = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    class Meta:
        indexes = [
            models.Index(fields=["magasin", "article"]),
            models.Index(fields=["article", "date_peremption"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(qte__gt=0),
                name="qte_positive"
            ),
        ]


class TransfertStock(models.Model):
    numero = models.IntegerField(unique=True, blank=False)
    magasin_source = models.ForeignKey(Magasin, on_delete=models.PROTECT, related_name="transferts_sortants")
    magasin_destination = models.ForeignKey(Magasin, on_delete=models.PROTECT, related_name="transferts_entrants")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey('users.CustomUser',
                                 related_name='transfertcreepar',
                                 on_delete=models.PROTECT)
    modifie_par = models.ForeignKey('users.CustomUser',
                                    blank=True, null=True,
                                    related_name='transfertmodpar',
                                    on_delete=models.PROTECT)
    actif = models.BooleanField(default=True)
    valide = models.BooleanField(default=False)

    def total_articles(self):
        return DetailsTransfertStock.objects.filter(transfert=self).count()

    @classmethod
    def get_next_num(cls):
        with transaction.atomic():
            last = cls.objects.select_for_update().aggregate(Max("numero"))["numero__max"]
            return (last + 1) if last else int(datetime.datetime.now().strftime('%y') + '0000')

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero:
            self.numero = self.get_next_num()

        super(TransfertStock, self).save(*args, **kwargs)


class DetailsTransfertStock(models.Model):
    transfert = models.ForeignKey(TransfertStock, on_delete=models.PROTECT)
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    qte = models.PositiveIntegerField()

    def get_my_lots(self):
        # Si on a utilisé 'prefetch_related' avec 'to_attr',
        # on filtre en Python plutôt qu'en SQL
        if hasattr(self.transfert, 'lots_reserves'):
            return [
                lot for lot in self.transfert.lots_reserves
                if lot.article_id == self.article_id
            ]
        # Fallback au cas où le prefetch n'a pas été fait
        return ReservationTransfertLot.objects.filter(
            transfert=self.transfert,
            article=self.article
        ).order_by('date_peremption')

    @transaction.atomic
    def add(self):
        detail, created = DetailsTransfertStock.objects.get_or_create(
            transfert=self.transfert,
            article=self.article,
            defaults={
                'qte': self.qte,
            }
        )

        if not created:
            detail.qte += self.qte
            detail.save()


class ReservationTransfertLot(models.Model):
    transfert = models.ForeignKey(TransfertStock, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    date_peremption = models.DateField()
    qte = models.PositiveIntegerField()