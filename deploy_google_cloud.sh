#!/usr/bin/env bash
# ==============================================================================
# SCRIPT DE DÉPLOIEMENT MÉDICO-LÉGAL 100% GOOGLE CLOUD & FIREBASE (CONBUSCA)
# ==============================================================================
set -e

PROJECT_ID=${GCP_PROJECT_ID:-"lalumiere-b68c9"}
REGION=${GCP_REGION:-"europe-west1"}
SERVICE_NAME="conbusca-api"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "=================================================================="
echo "🚀 DÉPLOIEMENT DU PROJET CONBUSCA EN ÉCOSYSTÈME 100% GOOGLE"
echo "Project GCP/Firebase: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "=================================================================="

# 1. Vérification des outils CLI requis
echo "🔍 [1/5] Vérification des CLI nécessaires..."
command -v gcloud >/dev/null 2>&1 || { echo "❌ gcloud CLI non installé. Veuillez installer Google Cloud SDK."; exit 1; }
command -v firebase >/dev/null 2>&1 || { echo "⚠️ firebase CLI non trouvé globalement, utilisation de npx firebase-tools"; }

# 2. Déploiement du Frontend Nuxt sur Firebase Hosting
echo "🌐 [2/5] Build et Déploiement Frontend Nuxt 3 vers Firebase Hosting..."
cd /home/adolphe/CONBUSCA/boutique
npm install
npm run generate || npm run build

if command -v firebase >/dev/null 2>&1; then
  firebase deploy --only hosting --project "${PROJECT_ID}"
else
  npx firebase-tools deploy --only hosting --project "${PROJECT_ID}"
fi
cd /home/adolphe/CONBUSCA

# 3. Build et Push de l'image Docker Django sur Google Cloud Artifact Registry / Container Registry
echo "🐳 [3/5] Build de l'image Docker Backend & Push sur Google Cloud Container Registry..."
gcloud builds submit --tag "${IMAGE_TAG}" --project "${PROJECT_ID}"

# 4. Déploiement / Mise à jour du service Google Cloud Run
echo "☁️ [4/5] Déploiement sur Google Cloud Run (${SERVICE_NAME})..."
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_TAG}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "DJANGO_SETTINGS_MODULE=esm.settings.production" \
    --project "${PROJECT_ID}"

# 5. Exécution des migrations Django sur Google Cloud SQL
echo "🗄️ [5/5] Exécution des migrations Django sur Cloud SQL..."
gcloud run jobs create conbusca-migrate-job \
    --image "${IMAGE_TAG}" \
    --region "${REGION}" \
    --command "python" \
    --args "manage.py","migrate","--noinput","--settings=esm.settings.production" \
    --project "${PROJECT_ID}" 2>/dev/null || \
gcloud run jobs update conbusca-migrate-job \
    --image "${IMAGE_TAG}" \
    --region "${REGION}" \
    --command "python" \
    --args "manage.py","migrate","--noinput","--settings=esm.settings.production" \
    --project "${PROJECT_ID}"

gcloud run jobs execute conbusca-migrate-job --region "${REGION}" --project "${PROJECT_ID}" --wait

echo "=================================================================="
echo "✅ DÉPLOIEMENT 100% GOOGLE CLOUD RÉUSSI AVEC SUCCÈS !"
echo "=================================================================="
