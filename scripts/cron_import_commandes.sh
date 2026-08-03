#!/usr/bin/env bash
# Script d'import des commandes Firestore → factures Conbuska
# Cron: */10 * * * * /var/www/esm/venv/bin/python /var/www/esm/manage.py importer_commandes --settings=esm.settings.production

set -euo pipefail
cd /var/www/esm
export DJANGO_SETTINGS_MODULE=esm.settings.production
source venv/bin/activate

python manage.py importer_commandes --settings=esm.settings.production >> /var/log/esm/import_commandes.log 2>&1
