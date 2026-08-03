#!/usr/bin/env bash
# Script de sauvegarde PostgreSQL quotidienne
# Cron: 0 2 * * * /var/www/esm/scripts/backup_v1.sh

set -euo pipefail
BACKUP_DIR="/var/backups/esm"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="esm_prod"
DB_USER="esm"
DB_HOST="127.0.0.1"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup of $DB_NAME"
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_DIR/esm_backup_${DATE}.dump" \
    --no-owner --no-privileges

BACKUP_FILE="$BACKUP_DIR/esm_backup_${DATE}.dump"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup complete: $BACKUP_FILE ($BACKUP_SIZE)"

# Also backup media files
tar czf "$BACKUP_DIR/esm_media_${DATE}.tar.gz" /var/www/esm/media/
echo "[$(date)] Media backup complete"

# Retention: keep last N days
find "$BACKUP_DIR" -name "esm_backup_*.dump" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "esm_media_*.tar.gz" -mtime +$RETENTION_DAYS -delete
echo "[$(date)] Old backups cleaned (> $RETENTION_DAYS days)"

# Verify backup
echo "[$(date)] Verifying backup..."
pg_restore --list "$BACKUP_FILE" > /dev/null 2>&1 && echo "[$(date)] Backup verification PASSED" || echo "[$(date)] Backup verification FAILED"
