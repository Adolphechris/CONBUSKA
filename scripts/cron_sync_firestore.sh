#!/usr/bin/env bash
# Script de synchronisation Firestore → articles publics
# Cron: */5 * * * * /var/www/esm/venv/bin/python /var/www/esm/manage.py sync_firestore --settings=esm.settings.production

set -euo pipefail
cd /var/www/esm
export DJANGO_SETTINGS_MODULE=esm.settings.production
source venv/bin/activate

python manage.py sync_firestore --settings=esm.settings.production >> /var/log/esm/sync_firestore.log 2>&1
