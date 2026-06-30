# ESM — Easy Stock Management

Système de gestion de stock, facturation, caisse, paie et e-commerce.

## 🚀 Démarrage rapide (développement)

```bash
cp .env.example .env     # Configurer les variables d'environnement
python3 -m venv venv     # Créer l'environnement virtuel
source venv/bin/activate # Activer l'environnement
pip install -r requirements.txt
python3 manage.py migrate --settings=esm.settings.dev
python3 manage.py runserver
```

## 🏭 Déploiement (production)

```bash
# 1. Configurer l'environnement de production
#    Copier .env avec les bons secrets

# 2. Exécuter le script de déploiement
./scripts/deploy.sh --branch main

# 3. Vérifier l'état de l'application
./scripts/health_check.sh
```

### Script de déploiement (`scripts/deploy.sh`)

Le script de déploiement automatise les étapes suivantes :

1. **Prérequis** : vérifie que git, python3, pip3 sont installés
2. **Git** : checkout de la branche, pull des dernières modifications
3. **Dépendances** : installation via `pip install -r requirements.txt`
4. **Migrations** : application des migrations Django
5. **Statiques** : collecte des fichiers statiques
6. **Services** : redémarrage de Gunicorn, Celery, Nginx
7. **Health check** : vérification que l'application répond

Options :
- `--branch <nom>` : branche à déployer (défaut: main)
- `--dry-run` : simule le déploiement sans rien exécuter

### Script de health check (`scripts/health_check.sh`)

Vérifie 5 aspects critiques :

1. **HTTP** : l'application répond-elle sur `/health/` ?
2. **Base de données** : connexion PostgreSQL opérationnelle ?
3. **Redis** : le cache Redis répond-il ?
4. **Services** : Gunicorn, Celery, Nginx sont-ils actifs ?
5. **Ressources** : disque, mémoire RAM, charge CPU sous les seuils ?

## 🔧 Configuration

| Fichier | Usage |
|---------|-------|
| `esm/settings/base.py` | Configuration commune (tous les environnements) |
| `esm/settings/dev.py` | Développement local (DEBUG=True) |
| `esm/settings/prod.py` | Production (configuration existante) |
| `esm/settings/production.py` | Production enrichie (Redis, logging, email) |

### Variables d'environnement requises

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Clé secrète Django |
| `DB_NAME` | Nom de la base PostgreSQL |
| `DB_USER` | Utilisateur PostgreSQL |
| `DB_PASSWORD` | Mot de passe PostgreSQL |
| `DB_HOST` | Hôte PostgreSQL |
| `ALLOWED_HOSTS` | Hôtes autorisés (production) |

### Variables d'environnement optionnelles

| Variable | Défaut | Description |
|----------|--------|-------------|
| `DB_PORT` | `5432` | Port PostgreSQL |
| `DB_CONN_MAX_AGE` | `60` | Durée de vie des connexions DB (secondes) |
| `REDIS_URL` | `redis://127.0.0.1:6379/1` | URL de connexion Redis |
| `REDIS_HOST` | `127.0.0.1` | Hôte Redis |
| `REDIS_PORT` | `6379` | Port Redis |
| `LOG_FILE` | `/var/log/esm/django.log` | Chemin du fichier de log |
| `EMAIL_HOST` | `smtp.gmail.com` | Serveur SMTP |
| `EMAIL_PORT` | `587` | Port SMTP |
| `EMAIL_HOST_USER` | — | Utilisateur SMTP |
| `EMAIL_HOST_PASSWORD` | — | Mot de passe SMTP |
| `DEFAULT_FROM_EMAIL` | `noreply@esm.app` | Expéditeur par défaut |
| `STATIC_ROOT` | `/var/www/esm/static` | Répertoire des fichiers statiques |
| `MEDIA_ROOT` | `/var/www/esm/media` | Répertoire des fichiers media |
| `HEALTH_CHECK_URL` | `http://localhost:8000/health/` | URL pour le health check |

## 📁 Structure du projet

```
CONBUSCA/
├── esm/            # Configuration Django
├── applications/   # Modules métier (factures, caisse, etc.)
├── scripts/        # Scripts d'automatisation
│   ├── deploy.sh         # Déploiement automatisé
│   ├── health_check.sh   # Surveillance
│   ├── backup_v1.sh      # Sauvegarde
│   └── migrate_*.py      # Migration v1→v2
├── docs/           # Documentation
├── static/         # Fichiers statiques
├── templates/      # Templates Django
└── requirements.txt
```

## 🧪 Tests

```bash
python3 manage.py test --settings=esm.settings.dev
```
