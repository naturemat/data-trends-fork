#!/bin/bash
# backup_mongo.sh - Backup para MongoDB con tus credenciales específicas
# Usuario: Grupo1, Password: passGrupo1

# ============================================
# CONFIGURACIÓN - TUS CREDENCIALES REALES
# ============================================
PROJECT_DIR="/home/ubuntu/scraper"
BACKUP_ROOT="/home/ubuntu/backups"
CONTAINER_NAME="mongodb_scraper"
DB_NAME="scraper_db"                    
RETENTION_DAYS=7

# TUS CREDENCIALES
MONGO_USER="usuario"
MONGO_PASSWORD="contraseña"

# Directorios
BACKUP_DIR="${BACKUP_ROOT}/mongodb"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)
BACKUP_NAME="mongo_backup_${TIMESTAMP}"

# ============================================
# FUNCIÓN PARA LOGS
# ============================================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

# Entrar al directorio del proyecto
cd "$PROJECT_DIR"

log "=== INICIANDO BACKUP MONGODB ==="
log "Usuario: $MONGO_USER"
log "Base de datos: $DB_NAME"

# 1. Verificar que el contenedor está corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log "ERROR: Contenedor '${CONTAINER_NAME}' no está corriendo"
    exit 1
fi
log "✓ Contenedor MongoDB está activo"

# 2. Crear directorio del día
DAILY_DIR="${BACKUP_DIR}/${DATE_ONLY}"
mkdir -p "$DAILY_DIR"
log "✓ Directorio creado: $DAILY_DIR"

# 3. Crear backup con mongodump (CON TUS CREDENCIALES)
log "Ejecutando mongodump..."
if docker exec "$CONTAINER_NAME" mongodump \
    --username "$MONGO_USER" \
    --password "$MONGO_PASSWORD" \
    --authenticationDatabase admin \
    --db "$DB_NAME" \
    --gzip \
    --out "/tmp/${BACKUP_NAME}"; then
    log "✓ mongodump ejecutado exitosamente"
else
    log "✗ Error en mongodump. Verifica credenciales."
    exit 1
fi

# 4. Verificar que se crearon archivos
log "Verificando archivos creados..."
if docker exec "$CONTAINER_NAME" test -d "/tmp/${BACKUP_NAME}/${DB_NAME}"; then
    FILE_COUNT=$(docker exec "$CONTAINER_NAME" find "/tmp/${BACKUP_NAME}/${DB_NAME}" -name "*.bson.gz" 2>/dev/null | wc -l)
    log "✓ Se crearon $FILE_COUNT archivos .bson.gz"
    
    # Listar colecciones backup
    log "Colecciones backup:"
    docker exec "$CONTAINER_NAME" find "/tmp/${BACKUP_NAME}/${DB_NAME}" -name "*.bson.gz" 2>/dev/null | \
        xargs -I {} basename {} .bson.gz | sed 's/^/  • /'
else
    log "✗ No se creó el directorio de backup"
    exit 1
fi

# 5. Copiar backup al host
log "Copiando backup al host..."
if docker cp "${CONTAINER_NAME}:/tmp/${BACKUP_NAME}" "$DAILY_DIR/"; then
    log "✓ Backup copiado a host"
else
    log "✗ Error copiando backup"
    exit 1
fi

# 6. Crear archivo tar comprimido
log "Comprimiendo backup..."
cd "$DAILY_DIR"
if tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"; then
    # Calcular tamaño
    BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    log "✓ Backup comprimido: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"
else
    log "✗ Error creando archivo tar.gz"
    exit 1
fi

# 7. Verificar integridad del tar.gz
log "Verificando integridad..."
if tar -tzf "${BACKUP_NAME}.tar.gz" > /dev/null 2>&1; then
    FILE_COUNT=$(tar -tzf "${BACKUP_NAME}.tar.gz" | wc -l)
    log "✓ Archivo válido con $FILE_COUNT archivos internos"
else
    log "✗ Archivo corrupto"
    exit 1
fi

# 8. Limpiar directorio temporal (sin comprimir)
rm -rf "${BACKUP_NAME}"
log "✓ Directorio temporal limpiado"

# 9. Limpiar del contenedor
docker exec "$CONTAINER_NAME" rm -rf "/tmp/${BACKUP_NAME}"
log "✓ Limpieza en contenedor completada"

# 10. Eliminar backups antiguos
log "Limpiando backups antiguos (más de $RETENTION_DAYS días)..."
OLD_COUNT=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f | wc -l)
find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -type d -name "202*" -empty -delete
NEW_COUNT=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f | wc -l)
ELIMINADOS=$((OLD_COUNT - NEW_COUNT))
log "✓ Eliminados $ELIMINADOS backups antiguos"

# 11. Mostrar resumen
log ""
log "=== RESUMEN DEL BACKUP ==="
log "Archivo creado: ${DAILY_DIR}/${BACKUP_NAME}.tar.gz"
log "Tamaño: ${BACKUP_SIZE}"
log "Base de datos: ${DB_NAME}"
log "Usuario: ${MONGO_USER}"
log ""
log "=== BACKUPS DISPONIBLES ==="
find "$BACKUP_DIR" -name "*.tar.gz" -type f -exec ls -lh {} \; | \
    awk '{print $6, $7, $8, " - ", $9, " ("$5")"}' | \
    sort -r | head -10 | sed 's/^/  /'

log ""
log "✅ BACKUP COMPLETADO EXITOSAMENTE"