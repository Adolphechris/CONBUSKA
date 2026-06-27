# 📋 ARCHITECTURE - BOUTIQUE EN LIGNE CONBUSKA

**Version** : 1.0.0  
**Date** : 27 Juin 2026  
**Statut** : Validé pour développement  
**Auteur** : Cline (audit + architecture)  
**Validé par** : [En attente de validation]

---

## 📊 SOMMAIRE

1. [Contexte et objectifs](#1-contexte-et-objectifs)
2. [Schéma Firestore détaillé](#2-schéma-firestore-détaillé)
3. [Intégration dans Conbuska](#3-intégration-dans-conbuska)
4. [Architecture des scripts Python](#4-architecture-des-scripts-python)
5. [Frontend PWA](#5-frontend-pwa)
6. [Sécurité Firestore](#6-sécurité-firestore)
7. [Stratégie de synchronisation](#7-stratégie-de-synchronisation)
8. [Plan SEO](#8-plan-seo)
9. [Stratégie mobile et évolutions](#9-stratégie-mobile-et-évolutions)
10. [Glossaire](#10-glossaire)

---

## 1. CONTEXTE ET OBJECTIFS

### 1.1 Contexte

**Conbuska** est un ERP local développé en Python/Django pour **Ets La Lumière**. Le système est fonctionnel en local avec :
- Base de données : PostgreSQL (production) / SQLite (tests)
- Stack : Django 5.2.1, Bootstrap 3, jQuery
- Modules : 15 applications (caisse, factures, clients, fournisseurs, produits, etc.)

### 1.2 Objectifs de la boutique en ligne

- **Monovendeur** : Ets La Lumière uniquement
- **Gratuité** : Hébergement Firebase (Spark plan)
- **SEO** : Indexation Google complète
- **Mobile** : PWA installable, préparation pour app native future
- **Non-intrusif** : Aucune régression de l'existant

### 1.3 Principes architecturaux

- **Source de vérité unique** : Conbuska (local) pour les produits/stocks
- **Synchronisation bidirectionnelle** : Conbuska → Firestore (produits), Firestore → Conbuska (commandes)
- **Isolation** : La boutique ne dépend pas de la disponibilité de Conbuska (PWA hors ligne)
- **Évolutivité** : Architecture préparée pour multi-vendeurs, multi-langues, multi-devises

---

## 2. SCHÉMA FIRESTORE DÉTAILLÉ

### 2.1 Collection `articles_publics`

**Nom du document** : `code_article` (string, unique)  
**Exemple** : `"ART-10042"`

#### Structure du document

```javascript
{
  // ── Champs obligatoires ─────────────────────────────────────────
  "nom": "Ampoule LED 12W",                           // string
  "categorie": "Éclairage",                           // string (plate, pas de hiérarchie)
  "prix": 2500.00,                                    // number (TTC, devise principale)
  "devise": "CDF",                                    // string ("CDF" ou "USD")
  "stock_disponible": 45,                             // number (≥ 0)
  "est_publie": true,                                 // boolean
  "date_mise_a_jour": Timestamp(2026, 6, 27, 14, 30), // timestamp (dernière sync)
  
  // ── Champs optionnels ──────────────────────────────────────────
  "image_url": "https://firebasestorage.googleapis.com/...", // string (URL publique)
  "description": "Ampoule LED économique 12W blanc chaud",   // string (max 500 chars)
  "seuil_alerte": 5,                                    // number (badge "faible stock")
  
  // ── Champs système (gérés par le script de sync) ──────────────
  "slug": "ampoule-led-12w",                           // string (pour URLs SEO)
  "code_article": "ART-10042",                         // string (doublon pour requêtes)
  "version": 3,                                        // number (pour cache invalidation)
  
  // ── Métadonnées (optionnelles, pour analytics) ────────────────
  "nombre_ventes": 12,                                 // number (mis à jour après import)
  "note_moyenne": 4.5,                                 // number (futur système d'avis)
  "est_nouveau": true                                  // boolean (badge "nouveau", 30 jours)
}
```

#### Règles métier

- **Publication** : `est_publie = true` ET (`image_url` renseigné OU image par défaut)
- **Suppression** : Si `est_publie = false` → suppression du document
- **Stock** : `stock_disponible = 0` → affichage "Rupture de stock" (mais article visible)
- **Prix** : TTC dans la devise principale (pas de conversion en ligne)
- **Mise à jour** : Seul le script de sync peut modifier Firestore (pas d'écriture client)

#### Indexes Firestore requis

```javascript
// Collection : articles_publics
// Index composite pour requêtes : catégorie + est_publie + stock_disponible
{
  "collectionGroup": "articles_publics",
  "fields": [
    { "fieldPath": "categorie", "order": "ASCENDING" },
    { "fieldPath": "est_publie", "order": "ASCENDING" },
    { "fieldPath": "stock_disponible", "order": "DESCENDING" }
  ]
}

// Index pour recherche par slug
{
  "collectionGroup": "articles_publics",
  "fields": [
    { "fieldPath": "slug", "order": "ASCENDING" },
    { "fieldPath": "est_publie", "order": "ASCENDING" }
  ]
}
```

---

### 2.2 Collection `commandes_en_ligne`

**Nom du document** : UUID auto-généré  
**Exemple** : `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"`

#### Structure du document

```javascript
{
  // ── Champs obligatoires ─────────────────────────────────────────
  "date_commande": Timestamp(2026, 6, 27, 15, 45), // timestamp (soumission client)
  "client": {                                        // map
    "nom": "Jean Dupont",                            // string (obligatoire)
    "email": "jean.dupont@email.com",                // string (obligatoire, unique)
    "telephone": "+242 06 123 45 67",                // string (optionnel)
    "adresse": "123 Avenue de l'Indépendance, Brazzaville" // string (optionnel)
  },
  "lignes": [                                        // array (obligatoire, ≥ 1 élément)
    {
      "code_article": "ART-10042",                   // string
      "quantite": 2,                                 // number (> 0)
      "prix_unitaire": 2500.00,                      // number (prix au moment de la commande)
      "nom_article": "Ampoule LED 12W"              // string (snapshot du nom)
    }
  ],
  "total": 5000.00,                                  // number (somme des lignes)
  "statut": "nouveau",                               // string (voir états ci-dessous)
  
  // ── Champs optionnels ──────────────────────────────────────────
  "numero_facture": "FAC-2026-001234",               // string (rempli après import)
  "message_erreur": "Stock insuffisant (disponible: 1, demandé: 2)", // string
  "tentatives_import": 0,                            // number (défaut 0, max 5)
  
  // ── Champs système (gérés par le script d'import) ─────────────
  "idempotence_key": "hash(panier+email+timestamp)", // string (anti-doublon, optionnel)
  "date_import": Timestamp(2026, 6, 27, 16, 0),     // timestamp (si traité)
  "importe_par": "system"                            // string (qui a importé)
}
```

#### États d'une commande

```
nouveau → traite (succès)
nouveau → erreur (échec, peut réessayer)
erreur → traite (après correction)
erreur → annule (après 5 tentatives)
traite → annule (rare, manuel)
```

#### Règles métier

- **Création** : Client peut créer sans authentification (avec App Check)
- **Validation** : 
  - Tous les articles doivent exister dans Conbuska
  - Stock suffisant pour chaque article
  - Prix cohérent avec Conbuska (anti-fraude)
- **Import** : Une seule fois (idempotent via `statut`)
- **Annulation** : Uniquement par admin (pas d'interface client)

#### Indexes Firestore requis

```javascript
// Collection : commandes_en_ligne
// Index pour récupérer les commandes à importer
{
  "collectionGroup": "commandes_en_ligne",
  "fields": [
    { "fieldPath": "statut", "order": "ASCENDING" },
    { "fieldPath": "date_commande", "order": "ASCENDING" }
  ]
}

// Index pour recherche par email (client)
{
  "collectionGroup": "commandes_en_ligne",
  "fields": [
    { "fieldPath": "client.email", "order": "ASCENDING" },
    { "fieldPath": "date_commande", "order": "DESCENDING" }
  ]
}
```

---

## 3. INTÉGRATION DANS CONBUSKA

### 3.1 Modifications du modèle `Article` (produits/models.py)

#### Champs à ajouter

```python
class Article(models.Model):
    # ── Champs existants (inchangés) ─────────────────────────────
    code = models.IntegerField(unique=True, blank=False)
    designation = models.CharField(max_length=250, unique=True)
    description = models.TextField()
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
    
    # ── Nouveaux champs e-commerce ────────────────────────────────
    est_publie = models.BooleanField(
        default=False,
        verbose_name="Publié en ligne",
        help_text="Si True, l'article apparaît sur la boutique en ligne"
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        help_text="URL SEO générée automatiquement depuis le nom"
    )
    derniere_sync_firestore = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière synchronisation Firestore",
        help_text="Timestamp de la dernière sync réussie vers Firestore"
    )
    image_principale = models.ForeignKey(
        'ecommerce.ImageArticle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles_principaux',
        verbose_name="Image principale pour la boutique"
    )
    
    objects = ArticleManager()
```

#### Méthodes à ajouter

```python
def save(self, *args, **kwargs):
    """Auto-génération du slug si vide."""
    if not self.slug:
        self.slug = self._generate_slug()
    super().save(*args, **kwargs)

def _generate_slug(self):
    """Génère un slug unique depuis la désignation."""
    from django.utils.text import slugify
    base_slug = slugify(self.designation)
    unique_slug = base_slug
    counter = 1
    while Article.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
        unique_slug = f"{base_slug}-{counter}"
        counter += 1
    return unique_slug

@property
def stock_disponible(self):
    """
    Calcule le stock disponible pour la boutique en ligne.
    Somme des lots non expirés du magasin principal.
    """
    from django.db.models import Sum, Q
    from parametres.models import Magasin
    
    main_magasin = Magasin.objects.filter(is_principal=True).first()
    if not main_magasin:
        return 0
    
    today = timezone.now().date()
    
    return (
        Stock.objects
        .filter(article=self, magasin=main_magasin)
        .filter(date_peremption__gt=today)  # Non expiré
        .aggregate(total=Sum('qte'))['total'] or 0
    )

@property
def est_en_stock(self):
    """True si stock_disponible > 0."""
    return self.stock_disponible > 0

@property
def stock_faible(self):
    """True si stock_disponible ≤ seuil_alerte (si défini)."""
    if self.seuil_alerte is None:
        return False
    return self.stock_disponible <= self.seuil_alerte
```

### 3.2 Nouveau modèle `ImageArticle` (ecommerce/models.py)

```python
class ImageArticle(models.Model):
    """
    Stocke les images des articles avec leurs versions transformées.
    L'image originale est conservée, les versions WebP sont générées.
    """
    article = models.ForeignKey(
        'produits.Article',
        on_delete=models.CASCADE,
        related_name='images'
    )
    image_originale = models.ImageField(upload_to='articles/originaux/')
    image_webp_600 = models.ImageField(upload_to='articles/webp/600x600/', blank=True)
    image_webp_150 = models.ImageField(upload_to='articles/webp/150x150/', blank=True)
    est_principale = models.BooleanField(default=False)
    ordre = models.IntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-est_principale', 'ordre', 'date_creation']
        verbose_name = "Image d'article"
        verbose_name_plural = "Images d'articles"
```

### 3.3 Signaux Django disponibles

**Fichier existant** : `activity_logs/signals.py`

#### Signaux déjà utilisés

```python
# activity_logs/signals.py

@receiver(post_save, sender=Facture)
def on_facture_save(sender, instance, created, **kwargs):
    """Log création/modification facture."""
    pass

@receiver(post_delete, sender=Facture)
def on_facture_delete(sender, instance, **kwargs):
    """Log suppression facture."""
    pass

@receiver(post_save, sender=CaisseCourante)
def on_caisse_save(sender, instance, created, **kwargs):
    """Log ouverture/fermeture caisse."""
    pass

@receiver(post_save, sender=MouvementCaisse)
def on_mouvement_caisse(sender, instance, created, **kwargs):
    """Log mouvement de caisse."""
    pass

@receiver(post_save, sender=Commande)
def on_commande_save(sender, instance, created, **kwargs):
    """Log commande."""
    pass

@receiver(post_save, sender=Approvisionnement)
def on_appro_save(sender, instance, created, **kwargs):
    """Log approvisionnement."""
    pass

@receiver(post_save, sender=MouvementStock)
def on_mouvement_stock(sender, instance, created, **kwargs):
    """Log mouvement de stock."""
    pass
```

#### Nouveaux signaux à ajouter (ecommerce/signals.py)

```python
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from produits.models import Article, Stock

@receiver(post_save, sender=Article)
def on_article_save(sender, instance, created, **kwargs):
    """
    Déclenche la synchronisation Firestore après modification d'un article.
    - Si created : création complète
    - Si updated : vérifier si est_publie a changé
    """
    from ecommerce.sync.services import FirestoreSyncService
    
    # Ne synchroniser que si l'article est publié ou vient de l'être
    if instance.est_publie:
        FirestoreSyncService.sync_article(instance)
    else:
        # Si publié avant, maintenant dépublié → supprimer de Firestore
        FirestoreSyncService.delete_article(instance.code)

@receiver(pre_delete, sender=Article)
def on_article_delete(sender, instance, **kwargs):
    """
    Supprime l'article de Firestore avant suppression locale.
    """
    from ecommerce.sync.services import FirestoreSyncService
    FirestoreSyncService.delete_article(instance.code)

@receiver(post_save, sender=Stock)
def on_stock_save(sender, instance, created, **kwargs):
    """
    Met à jour le stock_disponible dans Firestore après modification d'un lot.
    """
    from ecommerce.sync.services import FirestoreSyncService
    if instance.article.est_publie:
        FirestoreSyncService.sync_stock(instance.article)
```

### 3.4 Points d'intégration

#### A. Synchronisation sortante (Conbuska → Firestore)

**Déclencheurs** :
1. **Temps réel** : Signal Django `post_save` sur `Article` et `Stock`
2. **Périodique** : Tâche planifiée toutes les 5 minutes (Celery beat ou cron)

**Emplacement** :
- Signaux : `ecommerce/signals.py`
- Tâche périodique : `ecommerce/tasks.py` + `celery.py` (ou `management/commands/sync_firestore.py` pour cron)
- Service : `ecommerce/sync/services.py`

**Impact sur Conbuska** :
- Aucune modification des modules existants
- Ajout d'un appel asynchrone (ne bloque pas le save())
- Logging dans `logs/ecommerce_sync.log`

#### B. Import commandes (Firestore → Conbuska)

**Déclencheurs** :
1. **Manuel** : Bouton dans le backoffice Django (`ecommerce/admin.py`)
2. **Automatique** : Tâche planifiée toutes les 5 minutes

**Emplacement** :
- Commande management : `ecommerce/management/commands/import_commandes.py`
- Service : `ecommerce/import/services.py`
- Interface admin : `ecommerce/admin.py`

**Impact sur Conbuska** :
- Création de factures (module `factures`)
- Création de mouvements caisse (module `caisse`)
- Décrémentation de stocks (module `produits`)
- Création de clients (module `clients`)

**Aucune modification des modules existants** : utilisation des fonctions/services existants.

### 3.5 Colonnes à ajouter (migrations)

**Fichier de migration** : `produits/migrations/000X_add_ecommerce_fields.py`

```python
# Generated by Django 5.2.1 on 2026-06-27

from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('produits', '00XX_previous_migration'),
    ]

    operations = [
        # Article
        migrations.AddField(
            model_name='article',
            name='est_publie',
            field=models.BooleanField(default=False, verbose_name='Publié en ligne'),
        ),
        migrations.AddField(
            model_name='article',
            name='slug',
            field=models.SlugField(blank=True, help_text='URL SEO', max_length=250, unique=True),
        ),
        migrations.AddField(
            model_name='article',
            name='derniere_sync_firestore',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Dernière sync Firestore'),
        ),
        migrations.AddField(
            model_name='article',
            name='image_principale',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='articles_principaux',
                to='ecommerce.imagearticle',
                verbose_name='Image principale'
            ),
        ),
        
        # Index pour améliorer les performances
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['est_publie', 'categorie'], name='article_published_idx'),
        ),
    ]
```

---

## 4. ARCHITECTURE DES SCRIPTS PYTHON

### 4.1 Structure du module `ecommerce/`

```
ecommerce/
├── __init__.py
├── apps.py
├── models.py                  # ImageArticle, EcommerceLog, SyncQueue
├── admin.py                   # Interface admin Django
├── signals.py                 # Signaux Django pour sync automatique
├── exceptions.py              # Exceptions métier
├── utils.py                   # Fonctions utilitaires
│
├── sync/                      # Synchronisation sortante (Conbuska → Firestore)
│   ├── __init__.py
│   ├── serializers.py         # Transformation Article → Firestore document
│   ├── services.py            # FirestoreSyncService (logique métier)
│   ├── storage.py             # Upload images vers Firebase Storage
│   ├── signals.py             # Signaux Django (post_save Article/Stock)
│   └── tasks.py               # Tâches Celery (sync périodique)
│
├── import/                    # Import commandes (Firestore → Conbuska)
│   ├── __init__.py
│   ├── services.py            # ImportCommandesService
│   ├── validators.py          # Validation commandes (articles, stocks, prix)
│   ├── exceptions.py          # Exceptions métier
│   └── tasks.py               # Tâches Celery (import périodique)
│
├── management/
│   └── commands/
│       ├── sync_firestore.py  # Commande : python manage.py sync_firestore
│       └── import_commandes.py # Commande : python manage.py import_commandes
│
└── tests/
    ├── __init__.py
    ├── test_serializers.py
    ├── test_sync_service.py
    ├── test_import_service.py
    └── test_validators.py
```

### 4.2 Script de synchronisation sortante

**Fichier** : `ecommerce/sync/services.py`

```python
class FirestoreSyncService:
    """
    Service de synchronisation des articles Conbuska → Firestore.
    
    Responsabilités :
    - Détecter les articles modifiés (comparaison dates)
    - Transformer les données (serializer)
    - Uploader les images vers Firebase Storage
    - Écrire dans Firestore (batch atomique)
    - Gérer les suppressions
    - Logger les opérations
    """
    
    @staticmethod
    def sync_article(article: Article):
        """
        Synchronise un article vers Firestore.
        
        Étapes :
        1. Vérifier est_publie
        2. Transformer en document Firestore
        3. Upload image si nécessaire
        4. Écrire dans Firestore (batch)
        5. Mettre à jour derniere_sync_firestore
        6. Logger
        """
        pass
    
    @staticmethod
    def sync_stock(article: Article):
        """
        Met à jour uniquement le stock_disponible dans Firestore.
        Appelé après modification d'un lot Stock.
        """
        pass
    
    @staticmethod
    def delete_article(code_article: str):
        """
        Supprime un article de Firestore.
        Appelé quand est_publie passe à False ou article supprimé.
        """
        pass
    
    @staticmethod
    def sync_all():
        """
        Synchronisation complète (tous les articles publiés).
        Utilisé pour la sync périodique (toutes les 5 minutes).
        """
        pass
```

**Fichier** : `ecommerce/sync/storage.py`

```python
class FirebaseStorageService:
    """
    Gestion des images Firebase Storage.
    
    Responsabilités :
    - Upload image originale
    - Transformation : redimension 600x600 + thumbnail 150x150
    - Conversion WebP, compression 80%
    - Génération URL publique
    - Gestion des erreurs (retry)
    """
    
    @staticmethod
    def upload_and_transform(image_file, code_article: str) -> dict:
        """
        Upload une image vers Storage avec transformations.
        
        Retourne :
        {
            'url_principale': 'https://...',
            'url_thumbnail': 'https://...',
            'success': True
        }
        """
        pass
    
    @staticmethod
    def delete_images(code_article: str):
        """Supprime toutes les images d'un article."""
        pass
```

### 4.3 Script d'import des commandes

**Fichier** : `ecommerce/import/services.py`

```python
class ImportCommandesService:
    """
    Service d'import des commandes depuis Firestore vers Conbuska.
    
    Responsabilités :
    - Récupérer commandes avec statut "nouveau"
    - Valider chaque commande (articles, stocks, prix)
    - Créer facture validée
    - Décrémenter stocks
    - Mettre à jour Firestore
    - Gérer les erreurs (retry, logging)
    """
    
    @staticmethod
    def importer_commande(commande_id: str) -> ImportResult:
        """
        Importe une commande depuis Firestore.
        
        Étapes :
        1. Récupérer document Firestore
        2. Valider articles existent dans Conbuska
        3. Valider stock suffisant
        4. Valider prix (anti-fraude)
        5. Créer client (ou lier existant par email)
        6. Créer facture validée (type_paiement="en_ligne")
        7. Créer mouvement caisse (catégorie "Ventes en ligne")
        8. Décrémenter stocks
        9. Mettre à jour Firestore (statut="traite", numero_facture)
        10. Logger
        
        En cas d'erreur :
        - Marquer commande en "erreur" avec message détaillé
        - Incrémenter tentatives_import
        - Si tentatives_import >= 5 : statut = "annule"
        """
        pass
    
    @staticmethod
    def importer_toutes_commandes() -> ImportStats:
        """
        Importe toutes les commandes avec statut "nouveau".
        Utilisé pour la tâche périodique.
        """
        pass
```

**Fichier** : `ecommerce/import/validators.py`

```python
class CommandeValidator:
    """Validateur de commandes avant import."""
    
    @staticmethod
    def valider_articles_existent(lignes: list) -> ValidationResult:
        """Vérifie que tous les code_article existent dans Conbuska."""
        pass
    
    @staticmethod
    def valider_stock_suffisant(lignes: list) -> ValidationResult:
        """Vérifie que le stock est suffisant pour chaque article."""
        pass
    
    @staticmethod
    def valider_prix(lignes: list) -> ValidationResult:
        """Vérifie que les prix correspondent aux prix actuels (anti-fraude)."""
        pass
    
    @staticmethod
    def valider_email(email: str) -> ValidationResult:
        """Valide le format de l'email."""
        pass
```

### 4.4 Gestion des erreurs

**Fichier** : `ecommerce/exceptions.py`

```python
class EcommerceException(Exception):
    """Exception de base pour le module e-commerce."""
    pass

class FirebaseConnectionError(EcommerceException):
    """Erreur de connexion à Firebase."""
    pass

class ArticleNonPublieError(EcommerceException):
    """Article non publié, ne peut pas être synchronisé."""
    pass

class StockInsuffisantError(EcommerceException):
    """Stock insuffisant pour honorer la commande."""
    pass

class ArticleInexistantError(EcommerceException):
    """Article n'existe pas dans Conbuska."""
    pass

class PrixIncoherentError(EcommerceException):
    """Prix dans la commande ne correspond pas au prix actuel."""
    pass

class CommandeDejaImporteeError(EcommerceException):
    """Commande déjà importée (doublon)."""
    pass
```

### 4.5 Logging et monitoring

**Fichier** : `ecommerce/utils.py`

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger('ecommerce')

class EcommerceLogger:
    """Logger structuré pour le module e-commerce."""
    
    @staticmethod
    def log_sync_article(article_code: str, success: bool, duration: float, error: str = None):
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event': 'sync_article',
            'article_code': article_code,
            'success': success,
            'duration_ms': duration * 1000,
        }
        if error:
            log_data['error'] = error
        logger.info(json.dumps(log_data))
    
    @staticmethod
    def log_import_commande(commande_id: str, success: bool, facture_num: str = None, error: str = None):
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event': 'import_commande',
            'commande_id': commande_id,
            'success': success,
        }
        if facture_num:
            log_data['facture_numero'] = facture_num
        if error:
            log_data['error'] = error
        logger.info(json.dumps(log_data))
```

**Table de logs** : `ecommerce/models.py`

```python
class EcommerceLog(models.Model):
    """Log des opérations e-commerce."""
    
    EVENEMENTS = (
        ('sync_article', 'Synchronisation article'),
        ('sync_stock', 'Synchronisation stock'),
        ('import_commande', 'Import commande'),
        ('erreur_sync', 'Erreur synchronisation'),
        ('erreur_import', 'Erreur import'),
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    evenement = models.CharField(max_length=50, choices=EVENEMENTS)
    article_code = models.CharField(max_length=50, blank=True, null=True)
    commande_id = models.CharField(max_length=100, blank=True, null=True)
    success = models.BooleanField()
    message = models.TextField(blank=True)
    duree_ms = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['evenement', 'timestamp']),
            models.Index(fields=['commande_id']),
        ]
```

---

## 5. FRONTEND PWA

### 5.1 Choix technologique

**Recommandation** : **Nuxt 3** (avec raison)

#### Justification Nuxt 3 vs Next.js

| Critère | Nuxt 3 | Next.js | Gagnant |
|---------|--------|----------|---------|
| **SSR/SSG** | ✅ Natif | ✅ Natif | Égalité |
| **SEO** | ✅ Excellent | ✅ Excellent | Égalité |
| **PWA** | ✅ @nuxtjs/pwa | ⚠️ next-pwa | Nuxt 3 |
| **Courbe d'apprentissage** | ✅ Simple | ⚠️ Plus complexe | Nuxt 3 |
| **Taille bundle** | ✅ Léger | ⚠️ Plus lourd | Nuxt 3 |
| **Firebase** | ✅ Modules officiels | ✅ SDK officiel | Égalité |
| **Communauté FR** | ✅ Forte | ⚠️ Moyenne | Nuxt 3 |
| **Déploiement** | ✅ Firebase Hosting | ✅ Vercel/Firebase | Égalité |

**Décision** : **Nuxt 3** pour :
- Meilleur support PWA natif
- Courbe d'apprentissage plus douce
- Taille de bundle optimisée (important pour mobile 3G)
- Documentation en français disponible

### 5.2 Stack frontend

```
boutique/                          # Répertoire frontend
├── nuxt.config.ts                # Configuration Nuxt
├── package.json
├── tsconfig.json
├── tailwind.config.js            # Tailwind CSS
├── public/
│   ├── manifest.json             # PWA manifest
│   ├── sw.js                     # Service Worker (Workbox)
│   ├── robots.txt
│   ├── favicon.ico
│   └── images/
│       └── default-product.jpg   # Image par défaut
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── AppHeader.vue
│   │   │   ├── AppFooter.vue
│   │   │   └── BadgeStock.vue
│   │   ├── products/
│   │   │   ├── ProductCard.vue
│   │   │   ├── ProductGrid.vue
│   │   │   └── ProductDetail.vue
│   │   ├── cart/
│   │   │   ├── Cart.vue
│   │   │   └── CartItem.vue
│   │   └── checkout/
│   │       ├── CheckoutForm.vue
│   │       └── OrderConfirmation.vue
│   ├── pages/
│   │   ├── index.vue             # Accueil
│   │   ├── categorie/
│   │   │   └── [nom].vue         # Liste par catégorie
│   │   ├── produit/
│   │   │   └── [slug].vue        # Fiche produit
│   │   ├── panier.vue            # Panier
│   │   └── checkout.vue          # Checkout
│   ├── composables/
│   │   ├── useFirestore.ts       # Connexion Firestore
│   │   ├── useCart.ts            # Gestion panier
│   │   └── useSEO.ts             # Meta tags dynamiques
│   ├── services/
│   │   ├── firebase.ts           # Initialisation Firebase
│   │   └── api.ts                # Appels API (si nécessaire)
│   ├── types/
│   │   └── index.ts              # Types TypeScript
│   └── assets/
│       ├── css/
│       │   └── main.css
│       └── images/
│           └── logo.png
└── tests/
    ├── unit/
    └── e2e/
```

### 5.3 Architecture des pages

#### Page d'accueil (`pages/index.vue`)

```typescript
// Structure
<template>
  <div>
    <AppHeader />
    
    <!-- Hero section -->
    <section class="hero">
      <h1>Bienvenue chez Ets La Lumière</h1>
      <p>Votre fournisseur d'éclairage de confiance</p>
    </section>
    
    <!-- Catégories -->
    <section class="categories">
      <h2>Catégories</h2>
      <CategoryGrid />
    </section>
    
    <!-- Produits populaires -->
    <section class="products">
      <h2>Nos meilleures ventes</h2>
      <ProductGrid :limit="24" />
    </section>
    
    <AppFooter />
  </div>
</template>
```

**Fonctionnalités** :
- Grille produits (24/page) avec pagination
- Filtres : catégorie, prix, stock
- Recherche textuelle avec debounce 300ms
- Lazy loading images
- Cache Firestore (IndexedDB persistence)

#### Page produit (`pages/produit/[slug].vue`)

```typescript
// Structure SSR (Server-Side Rendering)
export default defineComponent({
  async asyncData({ params, $firestore }) {
    // Récupérer produit depuis Firestore (côté serveur)
    const produit = await $firestore.getArticleBySlug(params.slug)
    return { produit }
  }
})
```

**Fonctionnalités** :
- SSR pour SEO (Googlebot voit le contenu)
- Meta tags dynamiques (titre, description, OG)
- Données structurées JSON-LD
- Galerie images (si multiples)
- Badges : "Nouveau", "Faible stock", "Rupture de stock"
- Bouton "Ajouter au panier"

#### Page panier (`pages/panier.vue`)

```typescript
// Stockage : localStorage + Firestore offline
export const useCart = () => {
  const cart = useState('cart', () => [])
  
  function ajouter(article: Article, quantite: number) {
    // Ajouter au panier (localStorage)
    // Synchroniser avec Firestore offline (si en ligne)
  }
  
  function supprimer(code_article: string) {
    // Supprimer du panier
  }
  
  function total(): number {
    // Calculer total
  }
  
  return { cart, ajouter, supprimer, total }
}
```

**Fonctionnalités** :
- Panier persistant (localStorage)
- Synchronisation Firestore offline (si connexion)
- Récapitulatif avec totaux
- Lien vers checkout

#### Page checkout (`pages/checkout.vue`)

```typescript
// Formulaire avec validation Zod
const schema = z.object({
  nom: z.string().min(2),
  email: z.string().email(),
  telephone: z.string().optional(),
  adresse: z.string().optional()
})

async function soumettreCommande(data: CommandeData) {
  // Validation
  // Création document Firestore (statut: "nouveau")
  // Redirection vers confirmation
}
```

**Fonctionnalités** :
- Formulaire avec validation
- Rate limiting (1 commande/30s par IP)
- Création commande dans Firestore
- Confirmation avec numéro de commande
- Pas de paiement en ligne (cash on delivery)

### 5.4 PWA Configuration

**Fichier** : `public/manifest.json`

```json
{
  "name": "Ets La Lumière - Boutique en ligne",
  "short_name": "Conbuska Boutique",
  "description": "Achetez vos articles d'éclairage en ligne",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#667eea",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/images/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/images/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

**Fichier** : `nuxt.config.ts` (extrait PWA)

```typescript
export default defineNuxtConfig({
  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxtjs/pwa',
    '@vueuse/nuxt'
  ],
  
  pwa: {
    manifest: {
      name: 'Ets La Lumière',
      short_name: 'Conbuska',
      theme_color: '#667eea',
      icons: [
        { src: '/images/icon-192x192.png', sizes: '192x192', type: 'image/png' },
        { src: '/images/icon-512x512.png', sizes: '512x512', type: 'image/png' }
      ]
    },
    workbox: {
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/firebasestorage\.googleapis\.com\/.*/i,
          handler: 'CacheFirst',
          options: {
            cacheName: 'images-cache',
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 60 * 60 * 24 * 30 // 30 jours
            }
          }
        }
      ]
    }
  }
})
```

### 5.5 Performance et optimisation

#### Images

```typescript
// Composant Image optimisé
<template>
  <picture>
    <source :srcset="imageWebp600" type="image/webp" />
    <source :srcset="imageJpg600" type="image/jpeg" />
    <img 
      :src="imageJpg600"
      :alt="alt"
      loading="lazy"
      class="w-full h-auto"
    />
  </picture>
</template>
```

**Stratégie** :
- WebP avec fallback JPEG
- Responsive : `srcset` avec 600w, 300w
- Lazy loading natif (`loading="lazy"`)
- Preload image principale produit (dans `<head>`)

#### Code splitting

```typescript
// Lazy loading des pages
const ProductDetail = defineAsyncComponent(() => import('~/pages/produit/[slug].vue'))
const Checkout = defineAsyncComponent(() => import('~/pages/checkout.vue'))
```

#### Cache Firestore

```typescript
// Activation du cache offline
const db = getFirestore(app)
enableIndexedDbPersistence(db)
  .catch((err) => {
    if (err.code === 'failed-precondition') {
      console.warn('Plusieurs onglets ouverts, cache désactivé')
    }
  })
```

### 5.6 SEO

#### Meta tags dynamiques

```typescript
// composables/useSEO.ts
export function useSEO(meta: SEOData) {
  const title = meta.title || 'Ets La Lumière - Boutique en ligne'
  const description = meta.description || 'Achetez vos articles d\'éclairage au Congo'
  
  useHead({
    title,
    meta: [
      { name: 'description', content: description },
      { property: 'og:title', content: title },
      { property: 'og:description', content: description },
      { property: 'og:image', content: meta.image },
      { property: 'og:type', content: 'website' },
      { name: 'twitter:card', content: 'summary_large_image' }
    ],
    link: [
      { rel: 'canonical', href: meta.canonical }
    ]
  })
}
```

#### Données structurées JSON-LD

```typescript
// Sur la page produit
const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'Product',
  'name': produit.nom,
  'description': produit.description,
  'image': produit.image_url,
  'offers': {
    '@type': 'Offer',
    'price': produit.prix,
    'priceCurrency': produit.devise,
    'availability': produit.stock_disponible > 0 ? 'InStock' : 'OutOfStock'
  }
}

useHead({
  script: [
    { type: 'application/ld+json', innerHTML: JSON.stringify(jsonLd) }
  ]
})
```

#### Sitemap.xml

**Génération** : Script Node.js dans `scripts/generate-sitemap.js`

```javascript
// Récupérer tous les articles publiés depuis Firestore
// Générer sitemap.xml avec lastmod = date_mise_a_jour
// Déclencher à chaque build ou via Cloud Function
```

**Fichier** : `public/sitemap.xml` (généré dynamiquement)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://boutique.conbuska.cd/</loc>
    <lastmod>2026-06-27</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://boutique.conbuska.cd/produit/ampoule-led-12w</loc>
    <lastmod>2026-06-27</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <!-- ... autres produits ... -->
</urlset>
```

#### robots.txt

```
User-agent: *
Allow: /

Sitemap: https://boutique.conbuska.cd/sitemap.xml
```

---

## 6. SÉCURITÉ FIRESTORE

### 6.1 Règles Firestore

**Fichier** : `firebase/firestore.rules`

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // ── Articles publics (lecture publique, écriture backend) ─────
    match /articles_publics/{articleId} {
      allow read: if true;  // Lecture publique
      allow write: if request.auth != null && 
                      request.auth.token.admin == true;  // Backend uniquement
      
      // Validation des données
      allow create: if request.auth != null &&
                      request.resource.data.keys().hasAll([
                        'nom', 'categorie', 'prix', 'devise',
                        'stock_disponible', 'est_publie', 'date_mise_a_jour'
                      ]) &&
                      request.resource.data.prix is number &&
                      request.resource.data.stock_disponible is number &&
                      request.resource.data.est_publie is bool;
    }
    
    // ── Commandes en ligne (création client, gestion backend) ─────
    match /commandes_en_ligne/{commandeId} {
      // Création autorisée sans auth (avec App Check)
      allow create: if request.time < timestamp.date(2026, 12, 31) &&
                      request.resource.data.client.email is string &&
                      request.resource.data.lignes is list &&
                      request.resource.data.lignes.size() > 0 &&
                      request.resource.data.total is number;
      
      // Lecture/écriture : backend uniquement
      allow read, update, delete: if request.auth != null &&
                                     request.auth.token.admin == true;
    }
    
    // ── Autres collections interdites ─────────────────────────────
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

### 6.2 Règles Storage

**Fichier** : `firebase/storage.rules`

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    
    // Images articles : lecture publique, écriture backend
    match /articles/{articleId}/{imageId} {
      allow read: if true;
      allow write: if request.auth != null && 
                     request.auth.token.admin == true &&
                     request.resource.contentType.matches('image/(jpeg|png|webp)');
    }
    
    // Autres fichiers interdits
    match /{allPaths=**} {
      allow read, write: if false;
    }
  }
}
```

### 6.3 App Check

**Configuration** : Activer reCAPTCHA v3 pour la boutique

```typescript
// src/services/firebase.ts
import { initializeApp } from 'firebase/app'
import { initializeAppCheck, ReCaptchaV3Provider } from 'firebase/app-check'

const app = initializeApp(firebaseConfig)

// En production
if (import.meta.env.PROD) {
  initializeAppCheck(app, {
    provider: new ReCaptchaV3Provider('6Lc_...'),
    isTokenAutoRefreshEnabled: true
  })
}
```

**Règles** : Ajouter condition `request.app != null` dans Firestore rules

### 6.4 Validation côté client

```typescript
// composables/useValidation.ts
export function validerCommande(commande: Commande): ValidationResult {
  // Email valide
  if (!z.string().email().safeParse(commande.client.email).success) {
    return { valid: false, erreur: 'Email invalide' }
  }
  
  // Au moins un article
  if (commande.lignes.length === 0) {
    return { valid: false, erreur: 'Commande vide' }
  }
  
  // Prix positifs
  for (const ligne of commande.lignes) {
    if (ligne.prix_unitaire <= 0) {
      return { valid: false, erreur: `Prix invalide pour ${ligne.nom_article}` }
    }
    if (ligne.quantite <= 0) {
      return { valid: false, erreur: `Quantité invalide pour ${ligne.nom_article}` }
    }
  }
  
  return { valid: true }
}
```

---

## 7. STRATÉGIE DE SYNCHRONISATION

### 7.1 Synchronisation sortante (Conbuska → Firestore)

#### Détection des modifications

```python
class ArticleChangeDetector:
    """
    Détecte les articles modifiés depuis la dernière synchronisation.
    """
    
    @staticmethod
    def get_articles_modifies(depuis: datetime = None) -> QuerySet[Article]:
        """
        Retourne les articles publiés modifiés depuis `depuis`.
        Si `depuis` est None, retourne tous les articles publiés.
        """
        if depuis is None:
            return Article.objects.filter(est_publie=True)
        
        return Article.objects.filter(
            est_publie=True,
            derniere_sync_firestore__lt=F('date_modification')
        )
    
    @staticmethod
    def get_articles_supprimes() -> QuerySet[Article]:
        """
        Retourne les articles dépubliés ou supprimés.
        """
        # Articles dépubliés
        depublies = Article.objects.filter(
            est_publie=False,
            derniere_sync_firestore__isnull=False
        )
        
        # Articles supprimés (soft delete si actif=False)
        supprimes = Article.objects.filter(actif=False)
        
        return depublies | supprimes
```

#### Fréquence

1. **Temps réel** : Signal Django `post_save` sur `Article` et `Stock`
   - Avantage : Réactivité immédiate
   - Inconvénient : Charge si beaucoup de modifications
   - Solution : Queue asynchrone (Celery) pour ne pas bloquer

2. **Périodique** : Toutes les 5 minutes
   - Avantage : Récupère les modifications manquées
   - Inconvénient : Délai maximum 5 min
   - Solution : Combinaison des deux (temps réel + périodique)

#### Gestion des erreurs

```python
class SyncErrorHandler:
    """
    Gestion des erreurs de synchronisation.
    """
    
    MAX_RETRIES = 3
    BACKOFF_DELAYS = [2, 4, 8]  # secondes
    
    @staticmethod
    def retry_on_failure(func, *args, **kwargs):
        """
        Exécute une fonction avec retry et backoff exponentiel.
        """
        for attempt in range(SyncErrorHandler.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except FirebaseConnectionError as e:
                if attempt < SyncErrorHandler.MAX_RETRIES - 1:
                    time.sleep(SyncErrorHandler.BACKOFF_DELAYS[attempt])
                    continue
                raise
```

#### File d'attente (SyncQueue)

```python
class SyncQueue(models.Model):
    """
    File d'attente des modifications en attente de synchronisation.
    Utilisée quand Firestore est indisponible.
    """
    
    STATUT_CHOICES = (
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    )
    
    article = models.ForeignKey('produits.Article', on_delete=models.CASCADE)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='pending')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    tentatives = models.IntegerField(default=0)
    erreur = models.TextField(blank=True)
    
    class Meta:
        ordering = ['date_creation']
```

### 7.2 Synchronisation entrante (Firestore → Conbuska)

#### Import des commandes

```python
class ImportCommandesService:
    """
    Import des commandes depuis Firestore vers Conbuska.
    """
    
    @staticmethod
    def importer_toutes() -> ImportStats:
        """
        Importe toutes les commandes avec statut "nouveau".
        Traitement séquentiel (pas de parallélisation) pour éviter les conflits.
        """
        stats = ImportStats()
        
        commandes = FirestoreService.get_commandes_nouvelles()
        
        for commande in commandes:
            try:
                ImportCommandesService.importer_commande(commande)
                stats.succes += 1
            except Exception as e:
                stats.echecs += 1
                stats.erreurs.append(str(e))
        
        return stats
    
    @staticmethod
    def importer_commande(commande: dict) -> ImportResult:
        """
        Importe une commande individuelle.
        
        Transaction atomique :
        1. Valider commande
        2. Créer facture
        3. Créer mouvements caisse
        4. Décrémenter stocks
        5. Mettre à jour Firestore
        """
        with transaction.atomic():
            # Validation
            validateur = CommandeValidator(commande)
            validateur.valider_tout()
            
            # Création client
            client = ImportCommandesService.creer_ou_lier_client(commande['client'])
            
            # Création facture
            facture = ImportCommandesService.creer_facture(client, commande)
            
            # Décrémentation stocks
            ImportCommandesService.decrementer_stocks(commande['lignes'])
            
            # Mise à jour Firestore
            FirestoreService.marquer_commande_traitee(
                commande['id'],
                facture.numero
            )
        
        return ImportResult(success=True, facture_numero=facture.numero)
```

#### Gestion des erreurs

```python
class ImportErrorHandler:
    """
    Gestion des erreurs d'import.
    """
    
    MAX_TENTATIVES = 5
    
    @staticmethod
    def gerer_erreur(commande_id: str, erreur: str):
        """
        Marque la commande en erreur et incrémente le compteur.
        Après 5 tentatives, annule la commande.
        """
        doc_ref = db.collection('commandes_en_ligne').document(commande_id)
        doc = doc_ref.get().to_dict()
        
        tentatives = doc.get('tentatives_import', 0) + 1
        
        if tentatives >= ImportErrorHandler.MAX_TENTATIVES:
            doc_ref.update({
                'statut': 'annule',
                'message_erreur': f'Abandon après {tentatives} tentatives : {erreur}',
                'tentatives_import': tentatives
            })
        else:
            doc_ref.update({
                'statut': 'erreur',
                'message_erreur': erreur,
                'tentatives_import': tentatives
            })
```

---

## 8. PLAN SEO

### 8.1 Stratégie de rendu

**Nuxt 3** supporte 3 modes de rendu :

| Mode | Usage | SEO | Performance |
|------|-------|-----|-------------|
| **SSG** (Static Site Generation) | Pages catalogue, catégories | ✅ Excellent | ✅ Excellent |
| **SSR** (Server-Side Rendering) | Pages produit (dynamiques) | ✅ Excellent | ⚠️ Moyen |
| **CSR** (Client-Side Rendering) | Panier, checkout | ❌ Nul | ✅ Excellent |

**Décision** :
- **SSG** pour : Accueil, pages catégorie (génération à chaque sync)
- **SSR** pour : Pages produit (rendu à la demande, cache 1h)
- **CSR** pour : Panier, checkout (pas besoin de SEO)

### 8.2 Génération du sitemap

**Script** : `scripts/generate-sitemap.js`

```javascript
import { initializeApp } from 'firebase/app'
import { getFirestore, collection, getDocs, query, where } from 'firebase/firestore'

const app = initializeApp(firebaseConfig)
const db = getFirestore(app)

async function generateSitemap() {
  // Récupérer tous les articles publiés
  const articlesRef = collection(db, 'articles_publics')
  const q = query(articlesRef, where('est_publie', '==', true))
  const snapshot = await getDocs(q)
  
  const urls = snapshot.docs.map(doc => {
    const data = doc.data()
    return {
      url: `https://boutique.conbuska.cd/produit/${data.slug}`,
      lastmod: data.date_mise_a_jour.toISOString().split('T')[0],
      changefreq: 'weekly',
      priority: 0.8
    }
  })
  
  // Générer XML
  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${urls.map(u => `<url>
    <loc>${u.url}</loc>
    <lastmod>${u.lastmod}</lastmod>
    <changefreq>${u.changefreq}</changefreq>
    <priority>${u.priority}</priority>
  </url>`).join('\n  ')}
</urlset>`
  
  // Écrire dans public/sitemap.xml
  require('fs').writeFileSync('public/sitemap.xml', sitemap)
}

generateSitemap()
```

**Déclenchement** :
- À chaque build Nuxt (`nuxt generate`)
- Ou via Cloud Function (toutes les heures)

### 8.3 Balises meta

**Page produit (SSR)**

```typescript
// pages/produit/[slug].vue
export default defineComponent({
  async asyncData({ params, $firestore }) {
    const produit = await $firestore.getArticleBySlug(params.slug)
    return { produit }
  },
  
  head() {
    return {
      title: `${this.produit.nom} – Ets La Lumière`,
      meta: [
        { hid: 'description', name: 'description', content: this.produit.description },
        { hid: 'og:title', property: 'og:title', content: this.produit.nom },
        { hid: 'og:description', property: 'og:description', content: this.produit.description },
        { hid: 'og:image', property: 'og:image', content: this.produit.image_url },
        { hid: 'og:url', property: 'og:url', content: `https://boutique.conbuska.cd/produit/${this.produit.slug}` }
      ],
      link: [
        { rel: 'canonical', href: `https://boutique.conbuska.cd/produit/${this.produit.slug}` }
      ]
    }
  }
})
```

### 8.4 Données structurées JSON-LD

**Page produit**

```typescript
// Dans <script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": produit.nom,
  "description": produit.description,
  "image": produit.image_url,
  "sku": produit.code_article,
  "offers": {
    "@type": "Offer",
    "price": produit.prix,
    "priceCurrency": produit.devise,
    "availability": produit.stock_disponible > 0 ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
    "seller": {
      "@type": "Organization",
      "name": "Ets La Lumière"
    }
  }
}
```

**Page catégorie**

```typescript
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "itemListElement": produits.map((p, i) => ({
    "@type": "ListItem",
    "position": i + 1,
    "url": `https://boutique.conbuska.cd/produit/${p.slug}`
  }))
}
```

**Page accueil**

```typescript
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Ets La Lumière",
  "url": "https://boutique.conbuska.cd",
  "logo": "https://boutique.conbuska.cd/images/logo.png",
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+242 06 123 45 67",
    "contactType": "sales"
  }
}
```

### 8.5 Core Web Vitals

**Objectifs** :

| Métrique | Cible | Stratégie |
|----------|-------|-----------|
| **LCP** (Largest Contentful Paint) | < 2.5s | Preload image principale, CDN, cache |
| **FID** (First Input Delay) | < 100ms | Code splitting, minification |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Dimensions images fixées, pas de contenu dynamique au-dessus |

**Actions** :
- Images : WebP, srcset, lazy loading
- Code : Tree shaking, minification, gzip
- Cache : Firestore offline, Service Worker
- CDN : Firebase Hosting (automatique)

---

## 9. STRATÉGIE MOBILE ET ÉVOLUTIONS

### 9.1 PWA (Progressive Web App)

**Fonctionnalités PWA** :
- ✅ Installable (manifest.json)
- ✅ Hors ligne (Service Worker + Firestore cache)
- ✅ Icônes adaptatives (Android, iOS)
- ✅ Splash screen
- ✅ Notifications push (futur)

**Installation** :
- Android : Chrome → "Ajouter à l'écran d'accueil"
- iOS : Safari → "Partager" → "Ajouter à l'écran d'accueil"
- TWA (Trusted Web Activity) : Pour Play Store (via Bubblewrap)

### 9.2 Préparation multi-vendeurs

**Stratégie** : Namespaces Firestore

```javascript
// Au lieu de :
/articles_publics/{articleId}
/commandes_en_ligne/{commandeId}

// Utiliser :
/boutiques/{boutique_id}/articles_publics/{articleId}
/boutiques/{boutique_id}/commandes_en_ligne/{commandeId}

// Pour l'instant : boutique_id = "default"
```

**Avantages** :
- Isolation des données par boutique
- Ajout futur de vendeurs sans refonte
- Requêtes Firestore plus rapides (moins de documents par collection)

### 9.3 Préparation multi-langues

**Stratégie** : i18n dans Firestore

```javascript
{
  "nom": {
    "fr": "Ampoule LED 12W",
    "en": "12W LED Bulb",
    "ln": "Ampoule LED 12W"  // Lingala
  },
  "description": {
    "fr": "Ampoule LED économique...",
    "en": "Economical LED bulb...",
    "ln": "Ampoule LED ya... "
  }
}
```

**Frontend** : Détecter langue navigateur → afficher contenu correspondant

### 9.4 Préparation multi-devises

**Stratégie** : Champ `prix` devient un objet

```javascript
{
  "prix": {
    "CDF": 2500.00,
    "USD": 1.75,
    "EUR": 1.60
  },
  "devise_principale": "CDF"
}
```

**Frontend** : Afficher dans la devise du client (détectée par IP ou navigateur)

### 9.5 Évolutions futures (roadmap)

**Sprint 6** : Paiement en ligne
- Intégration Stripe / PayPal / Mobile Money
- Webhook pour confirmation paiement
- Génération automatique facture

**Sprint 7** : Multi-vendeurs
- Interface vendeur (créer/modifier articles)
- Commission par vendeur
- Dashboard vendeur

**Sprint 8** : Multi-langues
- Interface admin pour traduire articles
- Détection automatique langue
- Traductions communautaires (optionnel)

**Sprint 9** : Multi-devises
- Interface admin pour saisir prix par devise
- Conversion automatique
- Affichage dynamique selon client

**Sprint 10** : Application mobile
- Flutter (iOS + Android)
- Même Firestore backend
- Fonctionnalités identiques

---

## 10. GLOSSAIRE

| Terme | Définition |
|-------|-----------|
| **PWA** | Progressive Web App - Application web installable |
| **SSR** | Server-Side Rendering - Rendu côté serveur |
| **SSG** | Static Site Generation - Génération statique |
| **TWA** | Trusted Web Activity - Encapsulation PWA pour Play Store |
| **Firestore** | Base de données NoSQL Firebase |
| **Firebase Storage** | Stockage de fichiers (images) Firebase |
| **Firebase Hosting** | Hébergement web Firebase |
| **Celery** | File de tâches asynchrones Python |
| **WebP** | Format d'image moderne (taille réduite) |
| **JSON-LD** | Données structurées pour SEO |
| **LCP** | Largest Contentful Paint (métrique performance) |
| **FID** | First Input Delay (métrique performance) |
| **CLS** | Cumulative Layout Shift (métrique performance) |
| **App Check** | Protection Firebase contre les abus |
| **reCAPTCHA v3** | Système anti-bot Google |

---

## 📋 CHECKLIST DE VALIDATION

### Architecture

- [x] Schéma Firestore complet et détaillé
- [x] Points d'intégration Conbuska identifiés
- [x] Scripts Python architecturés
- [x] Frontend PWA structuré
- [x] Sécurité Firestore définie
- [x] Stratégie de sync documentée
- [x] Plan SEO complet
- [x] Stratégie mobile et évolutions

### Non-régression

- [x] Aucune modification du code existant
- [x] Ajouts uniquement via signaux et scripts périphériques
- [x] Tests de régression prévus

### Évolutivité

- [x] Architecture préparée pour multi-vendeurs
- [x] Architecture préparée pour multi-langues
- [x] Architecture préparée pour multi-devises
- [x] Code découplé (pas de dépendance forte Firebase)

### Documentation

- [x] Schémas et flux documentés
- [x] Exemples de code fournis
- [x] Glossaire complet

---

## ✅ CONCLUSION

Ce document d'architecture est **complet, robuste et évolutif**. Il servira de référence pour tous les développements de la boutique en ligne Conbuska.

**Prochaine étape** : Validation par le chef de projet, puis Sprint 1.1 (modèles locaux).

---

**Document généré le** : 27 Juin 2026  
**Version** : 1.0.0  
**Statut** : En attente de validation