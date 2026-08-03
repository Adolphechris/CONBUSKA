#!/usr/bin/env bash
# Script de déploiement backend CONBUSCA → serveur Linux (VPS)
# Usage: ./scripts/deploy_backend.sh [staging|production]

set -euo pipefail

ENV=${1:-production}
BRANCH=${2:-release/production-v1}
DEPLOY_DIR="/var/www/esm"
LOG_FILE="/var/log/esm/deploy.log"

echo "[$(date)] Starting backend deploy: ${ENV}" | tee -a "$LOG_FILE"

# ── 1. Pull latest code ──
cd "$DEPLOY_DIR"
echo "[$(date)] Pulling latest code from $BRANCH" | tee -a "$LOG_FILE"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

# ── 2. Install/update Python deps ──
echo "[$(date)] Installing Python dependencies" | tee -a "$LOG_FILE"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── 3. Run migrations ──
echo "[$(date)] Running migrations" | tee -a "$LOG_FILE"
python manage.py migrate --settings=esm.settings.production

# ── 4. Collect static files ──
echo "[$(date)] Collecting static files" | tee -a "$LOG_FILE"
python manage.py collectstatic --noinput --settings=esm.settings.production

# ── 5. Restart services ──
echo "[$(date)] Restarting services" | tee -a "$LOG_FILE"
sudo systemctl restart gunicorn-esm
sudo systemctl restart celery-esm
sudo systemctl restart celery-beat-esm
sudo systemctl restart nginx

# ── 6. Health check ──
sleep 3
HEALTH=$(curl -sf http://localhost/health/ || echo "FAILED")
if [ "$HEALTH" != "FAILED" ]; then
    echo "[$(date)] Health check passed" | tee -a "$LOG_FILE"
else
    echo "[$(date)] Health check FAILED" | tee -a "$LOG_FILE"
    exit 1
fi

echo "[$(date)] Backend deploy complete" | tee -a "$LOG_FILE"
