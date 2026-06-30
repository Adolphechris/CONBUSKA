#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# deploy.sh — Script de déploiement automatisé ESM (production)
# Usage : ./scripts/deploy.sh [--branch main] [--dry-run]
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Couleurs ─────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Configuration ───────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="${1:-main}"
DRY_RUN=false
[[ "${2:-}" == "--dry-run" ]] && DRY_RUN=true

# Charger les variables d'environnement
if [[ -f "$PROJECT_DIR/.env" ]]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

# ── Fonctions ───────────────────────────────────────────────────────
run() {
    if $DRY_RUN; then
        echo -e "${YELLOW}[DRY-RUN]${NC} $*"
    else
        "$@"
    fi
}

fail_on_dry_run() {
    if $DRY_RUN; then
        log_warn "DRY-RUN: l'étape suivante est simulée."
    fi
}

check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    command -v git     >/dev/null 2>&1 || { log_error "git est requis"; exit 1; }
    command -v python3 >/dev/null 2>&1 || { log_error "python3 est requis"; exit 1; }
    command -v pip3    >/dev/null 2>&1 || { log_error "pip3 est requis"; exit 1; }
    command -v psql    >/dev/null 2>&1 || log_warn "psql non trouvé (hors ligne de commande)"
    
    log_info "✅ Prérequis OK"
}

check_git_status() {
    log_info "Vérification du dépôt Git..."
    
    cd "$PROJECT_DIR"
    
    # Vérifier la branche
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
        log_warn "Branche actuelle: $CURRENT_BRANCH (attendue: $BRANCH)"
        run git checkout "$BRANCH"
    fi
    
    # Vérifier s'il y a des changements non commités
    if ! git diff-index --quiet HEAD --; then
        log_warn "Des changements locaux non commités existent."
        log_warn "▶  git stash ou commit avant de déployer."
        exit 1
    fi
    
    # Récupérer les dernières modifications
    log_info "Mise à jour depuis origin..."
    run git pull origin "$BRANCH"
    
    log_info "✅ Git OK (branche: $BRANCH, commit: $(git rev-parse --short HEAD))"
}

install_dependencies() {
    log_info "Installation des dépendances Python..."
    
    if [[ -d "$PROJECT_DIR/venv" ]]; then
        source "$PROJECT_DIR/venv/bin/activate"
    fi
    
    run pip3 install --upgrade pip
    run pip3 install -r "$PROJECT_DIR/requirements.txt" --no-cache-dir
    
    log_info "✅ Dépendances OK"
}

run_migrations() {
    log_info "Exécution des migrations Django..."
    
    cd "$PROJECT_DIR"
    run python3 manage.py migrate --settings=esm.settings.production --noinput
    
    log_info "✅ Migrations OK"
}

collect_static() {
    log_info "Collecte des fichiers statiques..."
    
    cd "$PROJECT_DIR"
    run python3 manage.py collectstatic --settings=esm.settings.production --noinput --clear
    
    log_info "✅ Statiques OK"
}

restart_services() {
    log_info "Redémarrage des services..."
    
    # Gunicorn
    if systemctl list-units --full -all 2>/dev/null | grep -q "gunicorn-esm"; then
        run sudo systemctl restart gunicorn-esm
        log_info "  ↳ gunicorn-esm redémarré"
    else
        log_warn "  ↳ Service gunicorn-esm introuvable — redémarrage manuel requis"
    fi
    
    # Celery
    if systemctl list-units --full -all 2>/dev/null | grep -q "celery-esm"; then
        run sudo systemctl restart celery-esm
        log_info "  ↳ celery-esm redémarré"
    fi
    
    # Nginx
    if systemctl list-units --full -all 2>/dev/null | grep -q "nginx"; then
        run sudo systemctl reload nginx
        log_info "  ↳ nginx rechargé"
    fi
    
    log_info "✅ Services redémarrés"
}

health_check() {
    log_info "Vérification de l'état de l'application..."
    
    HEALTH_URL="${HEALTH_CHECK_URL:-http://localhost:8000/health/}"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$HEALTH_URL" 2>/dev/null || echo "000")
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        log_info "✅ Health check OK (HTTP $HTTP_CODE)"
    else
        log_error "❌ Health check échoué (HTTP $HTTP_CODE)"
        return 1
    fi
}

notify_success() {
    COMMIT_HASH=$(cd "$PROJECT_DIR" && git rev-parse --short HEAD)
    log_info "══════════════════════════════════════════════"
    log_info "  🚀  Déploiement terminé avec succès !"
    log_info "  📌  Branche : $BRANCH"
    log_info "  📍  Commit  : $COMMIT_HASH"
    log_info "  🕐  Date    : $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "══════════════════════════════════════════════"
}

# ── Exécution principale ────────────────────────────────────────────
main() {
    echo ""
    echo "══════════════════════════════════════════════"
    echo "  🚀  Déploiement ESM"
    echo "  📦  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "══════════════════════════════════════════════"
    echo ""
    
    check_prerequisites
    echo ""
    
    check_git_status
    echo ""
    
    install_dependencies
    echo ""
    
    run_migrations
    echo ""
    
    collect_static
    echo ""
    
    restart_services
    echo ""
    
    health_check
    echo ""
    
    notify_success
}

main "$@"
