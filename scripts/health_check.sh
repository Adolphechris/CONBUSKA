#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# health_check.sh — Script de surveillance de l'état de l'application
# Usage : ./scripts/health_check.sh
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Couleurs ─────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
log_ok()    { echo -e "${GREEN}[OK]${NC}      $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}     $*"; }
log_error() { echo -e "${RED}[ERROR]${NC}    $*"; }

# ── Configuration ───────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEALTH_URL="${HEALTH_CHECK_URL:-http://localhost:8000/health/}"
TIMEOUT=10
MAX_RETRIES=3
SERVICES=("gunicorn-esm" "celery-esm" "nginx")
ALERTS=0

# ── Vérification 1 : Santé HTTP ─────────────────────────────────────
check_http_health() {
    echo ""
    echo "══════════════════════════════════════════════"
    echo "  🩺  Health Check ESM"
    echo "  🕐  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "══════════════════════════════════════════════"
    echo ""
    
    echo "── 1. Santé HTTP ──"
    local attempt=1
    while [[ $attempt -le $MAX_RETRIES ]]; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$HEALTH_URL" 2>/dev/null || echo "000")
        
        if [[ "$HTTP_CODE" == "200" ]]; then
            RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time "$TIMEOUT" "$HEALTH_URL" 2>/dev/null)
            log_ok "HTTP $HTTP_CODE — Temps de réponse: ${RESPONSE_TIME}s"
            break
        elif [[ "$HTTP_CODE" == "000" ]]; then
            log_warn "Tentative $attempt/$MAX_RETRIES — Pas de réponse"
        else
            log_warn "Tentative $attempt/$MAX_RETRIES — HTTP $HTTP_CODE"
        fi
        
        if [[ $attempt -eq $MAX_RETRIES ]]; then
            log_error "Santé HTTP indisponible après $MAX_RETRIES tentatives"
            ALERTS=$((ALERTS + 1))
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
}

# ── Vérification 2 : Base de données ────────────────────────────────
check_database() {
    echo ""
    echo "── 2. Base de données ──"
    
    if command -v psql &>/dev/null; then
        DB_NAME="${DB_NAME:-esm}"
        DB_USER="${DB_USER:-postgres}"
        DB_HOST="${DB_HOST:-localhost}"
        DB_PORT="${DB_PORT:-5432}"
        
        if PGPASSWORD="${DB_PASSWORD:-}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &>/dev/null; then
            DB_SIZE=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | tr -d ' ')
            CONN_COUNT=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | tr -d ' ')
            log_ok "Connexion OK — Taille: ${DB_SIZE:-?} — Connexions actives: ${CONN_COUNT:-?}"
        else
            log_error "Impossible de se connecter à la base de données"
            ALERTS=$((ALERTS + 1))
        fi
    else
        log_warn "psql non installé — vérification DB ignorée"
    fi
}

# ── Vérification 3 : Redis ─────────────────────────────────────────
check_redis() {
    echo ""
    echo "── 3. Redis ──"
    
    local REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/1}"
    
    if command -v redis-cli &>/dev/null; then
        local REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
        local REDIS_PORT="${REDIS_PORT:-6379}"
        
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q "PONG"; then
            local REDIS_MEMORY
            REDIS_MEMORY=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" info memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 || echo "?")
            log_ok "Connexion OK — Mémoire utilisée: ${REDIS_MEMORY}"
        else
            log_error "Redis ne répond pas"
            ALERTS=$((ALERTS + 1))
        fi
    else
        log_warn "redis-cli non installé — vérification Redis ignorée"
    fi
}

# ── Vérification 4 : Services système ───────────────────────────────
check_services() {
    echo ""
    echo "── 4. Services système ──"
    
    if ! command -v systemctl &>/dev/null; then
        log_warn "systemctl non disponible — vérification des services ignorée"
        return
    fi
    
    for SERVICE in "${SERVICES[@]}"; do
        if systemctl list-units --full -all 2>/dev/null | grep -q "$SERVICE"; then
            local STATUS
            STATUS=$(systemctl is-active "$SERVICE" 2>/dev/null || echo "unknown")
            if [[ "$STATUS" == "active" ]]; then
                log_ok "$SERVICE: actif"
            else
                log_error "$SERVICE: $STATUS"
                ALERTS=$((ALERTS + 1))
            fi
        else
            log_warn "$SERVICE: non trouvé"
        fi
    done
}

# ── Vérification 5 : Disque et mémoire ──────────────────────────────
check_resources() {
    echo ""
    echo "── 5. Ressources système ──"
    
    # Disque
    local DISK_USAGE
    DISK_USAGE=$(df -h "$PROJECT_DIR" | awk 'NR==2 {print $5}' | tr -d '%' 2>/dev/null || echo "?")
    if [[ "$DISK_USAGE" =~ ^[0-9]+$ ]]; then
        if [[ "$DISK_USAGE" -gt 90 ]]; then
            log_error "Espace disque: ${DISK_USAGE}% (seuil: 90%)"
            ALERTS=$((ALERTS + 1))
        elif [[ "$DISK_USAGE" -gt 80 ]]; then
            log_warn "Espace disque: ${DISK_USAGE}% (seuil: 80%)"
        else
            log_ok "Espace disque: ${DISK_USAGE}%"
        fi
    else
        log_warn "Impossible de déterminer l'utilisation disque"
    fi
    
    # Mémoire
    if command -v free &>/dev/null; then
        local MEM_INFO
        MEM_INFO=$(free -m | awk 'NR==2{printf "%.0f", $3*100/$2}' 2>/dev/null || echo "?")
        if [[ "$MEM_INFO" =~ ^[0-9]+$ ]]; then
            if [[ "$MEM_INFO" -gt 90 ]]; then
                log_error "Mémoire RAM: ${MEM_INFO}% (seuil: 90%)"
                ALERTS=$((ALERTS + 1))
            elif [[ "$MEM_INFO" -gt 80 ]]; then
                log_warn "Mémoire RAM: ${MEM_INFO}% (seuil: 80%)"
            else
                log_ok "Mémoire RAM: ${MEM_INFO}%"
            fi
        fi
    fi
    
    # Charge CPU (load average 1min)
    if [[ -f /proc/loadavg ]]; then
        local CPU_LOAD
        CPU_LOAD=$(awk '{print $1}' /proc/loadavg 2>/dev/null || echo "?")
        local CPU_CORES
        CPU_CORES=$(nproc 2>/dev/null || echo 1)
        if [[ "$CPU_LOAD" != "?" ]]; then
            local CPU_PERCENT
            CPU_PERCENT=$(echo "$CPU_LOAD $CPU_CORES" | awk '{printf "%.0f", ($1/$2)*100}' 2>/dev/null || echo "?")
            if [[ "$CPU_PERCENT" =~ ^[0-9]+$ ]]; then
                if [[ "$CPU_PERCENT" -gt 90 ]]; then
                    log_error "Charge CPU: ${CPU_PERCENT}% (seuil: 90%)"
                    ALERTS=$((ALERTS + 1))
                elif [[ "$CPU_PERCENT" -gt 80 ]]; then
                    log_warn "Charge CPU: ${CPU_PERCENT}% (seuil: 80%)"
                else
                    log_ok "Charge CPU: ${CPU_PERCENT}%"
                fi
            fi
        fi
    fi
}

# ── Rapport final ───────────────────────────────────────────────────
print_summary() {
    echo ""
    echo "══════════════════════════════════════════════"
    if [[ "$ALERTS" -eq 0 ]]; then
        echo "  ✅  RESULTAT: TOUT EST OK (0 alerte)"
    elif [[ "$ALERTS" -eq 1 ]]; then
        echo "  ⚠️   RESULTAT: $ALERTS alerte détectée"
    else
        echo "  🚨  RESULTAT: $ALERTS alertes détectées"
    fi
    echo "  🕐  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "══════════════════════════════════════════════"
    echo ""
    
    return "$ALERTS"
}

# ── Exécution principale ────────────────────────────────────────────
main() {
    check_http_health
    check_database
    check_redis
    check_services
    check_resources
    print_summary
}

main "$@"
