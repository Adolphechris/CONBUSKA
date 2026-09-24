# Image officielle Python 3.12 d'origine Debian Bookworm slim
FROM python:3.12-slim

# Éviter l'écriture des fichiers .pyc et forcer l'affichage immédiat des logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système requises pour PostgreSQL, ReportLab, Cairo, Pango et Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    libcairo2 \
    libpango-1.0-0 \
    pangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'intégralité du projet Django dans le conteneur
COPY . /app/

# Exécuter collectstatic pour regrouper les statics si besoin
RUN python manage.py collectstatic --noinput --settings=esm.settings.production || true

# Exposer le port (utilisé par Cloud Run)
EXPOSE 8080

# Démarrer le serveur Gunicorn configuré pour Google Cloud Run
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 3 --threads 8 --timeout 0 esm.wsgi:application
