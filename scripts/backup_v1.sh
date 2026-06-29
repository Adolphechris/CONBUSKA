#!/bin/bash
# Script de sauvegarde avant migration v2.0
# Usage: ./scripts/backup_v1.sh

set -e  # Arrêter en cas d'erreur

echo "============================================================"
echo "📦 SAUVEGARDE AVANT MIGRATION v1.0 → v2.0"
echo "============================================================"
echo ""

# Variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
BACKUP_PREFIX="esm_v1_backup_${TIMESTAMP}"

# Créer le dossier de sauvegarde
mkdir -p ${BACKUP_DIR}

echo "📁 Dossier de sauvegarde: ${BACKUP_DIR}/"
echo ""

# 1. Sauvegarde de la base de données PostgreSQL
echo "💾 Sauvegarde de la base de données..."
DB_NAME=${DB_NAME:-esm}
DB_USER=${DB_USER:-postgres}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}

pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-acl \
    -f ${BACKUP_DIR}/${BACKUP_PREFIX}_database.dump

echo "   ✅ Base de données sauvegardée: ${BACKUP_PREFIX}_database.dump"
echo ""

# 2. Sauvegarde des fichiers media
echo "📸 Sauvegarde des fichiers media..."
if [ -d "media" ]; then
    tar -czf ${BACKUP_DIR}/${BACKUP_PREFIX}_media.tar.gz media/
    echo "   ✅ Media sauvegardés: ${BACKUP_PREFIX}_media.tar.gz"
else
    echo "   ℹ️  Aucun dossier media trouvé"
fi
echo ""

# 3. Sauvegarde de la configuration
echo "⚙️  Sauvegarde de la configuration..."
tar -czf ${BACKUP_DIR}/${BACKUP_PREFIX}_config.tar.gz \
    .env* \
    esm/settings/ \
    requirements.txt \
    manage.py \
    --exclude=*.pyc \
    --exclude=__pycache__
echo "   ✅ Configuration sauvegardée: ${BACKUP_PREFIX}_config.tar.gz"
echo ""

# 4. Créer un tag Git
echo "🏷️  Création du tag Git..."
git tag -a "v1.0.0_backup_${TIMESTAMP}" -m "Backup avant migration v2.0 - ${TIMESTAMP}"
echo "   ✅ Tag Git créé: v1.0.0_backup_${TIMESTAMP}"
echo ""

# 5. Générer le manifeste de sauvegarde
echo "📄 Génération du manifeste..."
cat > ${BACKUP_DIR}/${BACKUP_PREFIX}_manifest.txt << EOF
# Manifeste de Sauvegarde ESM v1.0
# Date: $(date '+%Y-%m-%d %H:%M:%S')

## Informations
- Version: 1.0.0
- Branche: $(git branch --show-current)
- Commit: $(git rev-parse HEAD)
- Django: $(python3 -c "import django; print(django.get_version())")

## Fichiers sauvegardés
1. ${BACKUP_PREFIX}_database.dump - Base de données PostgreSQL
2. ${BACKUP_PREFIX}_media.tar.gz - Fichiers media
3. ${BACKUP_PREFIX}_config.tar.gz - Configuration et settings

## Tag Git
- v1.0.0_backup_${TIMESTAMP}

## Procédure de restauration
1. Restaurer la base: pg_restore -U postgres -d esm ${BACKUP_PREFIX}_database.dump
2. Extraire media: tar -xzf ${BACKUP_PREFIX}_media.tar.gz
3. Extraire config: tar -xzf ${BACKUP_PREFIX}_config.tar.gz
4. Checkout tag: git checkout v1.0.0_backup_${TIMESTAMP}

## Vérification
- [ ] Base de données restaurée
- [ ] Fichiers media restaurés
- [ ] Configuration restaurée
- [ ] Tests fonctionnels passés

## Notes
- Conserver cette sauvegarde jusqu'à validation de la v2.0
- Tester la procédure de rollback avant migration
EOF

echo "   ✅ Manifeste créé: ${BACKUP_PREFIX}_manifest.txt"
echo ""

# 6. Afficher le résumé
echo "============================================================"
echo "✅ SAUVEGARDE TERMINÉE"
echo "============================================================"
echo ""
echo "📦 Fichiers créés dans ${BACKUP_DIR}/:"
ls -lh ${BACKUP_DIR}/${BACKUP_PREFIX}*
echo ""
echo "📋 Prochaines étapes:"
echo "   1. Vérifier les fichiers de sauvegarde"
echo "   2. Tester la procédure de rollback"
echo "   3. Lancer la migration: python3 scripts/migrate_v1_to_v2.py"
echo ""
echo "⚠️  IMPORTANT: Ne pas supprimer ces sauvegardes avant validation v2.0"
echo "============================================================"