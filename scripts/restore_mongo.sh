#!/bin/bash
# restore_mongo.sh
# Uso: ./restore_mongo.sh [fecha_AAAAMMDD | latest]

BACKUP_ROOT="/home/ubuntu/backups"
PROJECT_DIR="/home/ubuntu/scraper"
#TUS CREDENCIALES
MONGO_USER="usuario"
MONGO_PASSWORD="contraseña"
DB_NAME="scraper_db"

if [ -z "$1" ]; then
    echo "Uso: $0 [fecha_AAAAMMDD | latest]"
    echo ""
    echo "Backups disponibles:"
    echo "-------------------"
    find "$BACKUP_ROOT/mongodb" -name "*.tar.gz" -type f | \
        xargs -I {} basename {} .tar.gz | \
        sed 's/mongo_backup_//' | \
        sort -r | head -10 | \
        awk '{print "  " substr($1,1,8) " - " substr($1,10,6)}'
    exit 1
fi

# Buscar backup
if [ "$1" = "latest" ]; then
    BACKUP_FILE=$(find "$BACKUP_ROOT/mongodb" -name "*.tar.gz" -type f | sort -r | head -1)
else
    DATE="$1"
    BACKUP_FILE=$(find "$BACKUP_ROOT/mongodb" -name "*${DATE}*.tar.gz" -type f | sort -r | head -1)
fi

if [ -z "$BACKUP_FILE" ]; then
    echo "Error: No se encontró backup"
    exit 1
fi

echo "=== RESTAURACIÓN MONGODB ==="
echo "Backup: $(basename "$BACKUP_FILE")"
echo "Base de datos: $DB_NAME"
echo ""
echo "⚠️  ADVERTENCIA: Esto SOBREESCRIBIRÁ la base de datos $DB_NAME"
echo "¿Continuar? (s/N): "
read -r CONFIRM

if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
    echo "Cancelado."
    exit 0
fi

# Extraer backup temporalmente
TEMP_DIR="/tmp/mongo_restore_$$"
mkdir -p "$TEMP_DIR"
echo "Extrayendo backup..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Restaurar
echo "Restaurando base de datos..."
cd "$PROJECT_DIR"

docker exec mongodb_scraper mongorestore \
    --username "$MONGO_USER" \
    --password "$MONGO_PASSWORD" \
    --authenticationDatabase admin \
    --db "$DB_NAME" \
    --gzip \
    --drop \
    --dir "/tmp/mongo_restore_$$/$(basename "$BACKUP_FILE" .tar.gz)/$DB_NAME"

# Limpiar
rm -rf "$TEMP_DIR"
docker exec mongodb_scraper rm -rf "/tmp/mongo_restore_$$"

echo ""
echo "✅ Restauración completada!"
echo ""
echo "Verificar con:"
echo "  docker-compose exec mongodb mongosh -u $MONGO_USER -p $MONGO_PASSWORD --authenticationDatabase admin $DB_NAME --eval 'show collections'"