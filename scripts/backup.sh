#!/bin/bash
# OpenMail Platform Backup Script

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/openmail}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}📦 OpenMail Backup${NC}"
echo "===================="

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
backup_postgres() {
    echo -e "\n${YELLOW}Backing up PostgreSQL...${NC}"
    
    docker compose exec -T postgres pg_dump -U openmail openmail | \
        gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"
    
    echo -e "${GREEN}✓ PostgreSQL backed up${NC}"
}

# Backup Redis
backup_redis() {
    echo -e "\n${YELLOW}Backing up Redis...${NC}"
    
    # Trigger save
    docker compose exec -T redis redis-cli SAVE
    
    # Copy dump file
    docker compose cp redis:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"
    
    echo -e "${GREEN}✓ Redis backed up${NC}"
}

# Backup mail data
backup_maildata() {
    echo -e "\n${YELLOW}Backing up mail data...${NC}"
    
    # This backs up the mail volume
    docker run --rm \
        -v openmail_mail_data:/data \
        -v "$BACKUP_DIR":/backup \
        alpine tar czf "/backup/maildata_$DATE.tar.gz" -C /data .
    
    echo -e "${GREEN}✓ Mail data backed up${NC}"
}

# Backup attachments (MinIO)
backup_attachments() {
    echo -e "\n${YELLOW}Backing up attachments...${NC}"
    
    docker run --rm \
        -v openmail_minio_data:/data \
        -v "$BACKUP_DIR":/backup \
        alpine tar czf "/backup/attachments_$DATE.tar.gz" -C /data .
    
    echo -e "${GREEN}✓ Attachments backed up${NC}"
}

# Backup configuration
backup_config() {
    echo -e "\n${YELLOW}Backing up configuration...${NC}"
    
    tar czf "$BACKUP_DIR/config_$DATE.tar.gz" \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='.env' \
        .
    
    echo -e "${GREEN}✓ Configuration backed up${NC}"
}

# Clean old backups
cleanup_old_backups() {
    echo -e "\n${YELLOW}Cleaning old backups (>$RETENTION_DAYS days)...${NC}"
    
    find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
    
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Main backup
main() {
    cd "$(dirname "$0")/.."
    
    echo "Backup directory: $BACKUP_DIR"
    echo "Date: $DATE"
    
    backup_postgres
    backup_redis
    backup_maildata
    backup_attachments
    backup_config
    cleanup_old_backups
    
    # Calculate total size
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
    
    echo -e "\n${GREEN}🎉 Backup Complete!${NC}"
    echo "===================="
    echo "Files created:"
    ls -lh "$BACKUP_DIR"/*_$DATE* 2>/dev/null || echo "  No files for this date"
    echo ""
    echo "Total backup size: $TOTAL_SIZE"
}

# Restore function
restore() {
    RESTORE_DATE="$1"
    
    if [ -z "$RESTORE_DATE" ]; then
        echo "Usage: $0 --restore <DATE>"
        echo "Available backups:"
        ls -1 "$BACKUP_DIR" | grep -oP '\d{8}_\d{6}' | sort -u
        exit 1
    fi
    
    echo -e "${YELLOW}⚠️  This will overwrite current data!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
    
    cd "$(dirname "$0")/.."
    
    # Stop services
    docker compose down
    
    # Restore PostgreSQL
    echo "Restoring PostgreSQL..."
    docker compose up -d postgres
    sleep 5
    gunzip -c "$BACKUP_DIR/postgres_$RESTORE_DATE.sql.gz" | \
        docker compose exec -T postgres psql -U openmail openmail
    
    # Restore Redis
    echo "Restoring Redis..."
    docker compose cp "$BACKUP_DIR/redis_$RESTORE_DATE.rdb" redis:/data/dump.rdb
    
    # Restore mail data
    echo "Restoring mail data..."
    docker run --rm \
        -v openmail_mail_data:/data \
        -v "$BACKUP_DIR":/backup \
        alpine sh -c "rm -rf /data/* && tar xzf /backup/maildata_$RESTORE_DATE.tar.gz -C /data"
    
    # Start services
    docker compose up -d
    
    echo -e "${GREEN}✓ Restore complete!${NC}"
}

# Parse arguments
case "${1:-}" in
    --restore)
        restore "$2"
        ;;
    --postgres-only)
        backup_postgres
        ;;
    --redis-only)
        backup_redis
        ;;
    --mail-only)
        backup_maildata
        ;;
    *)
        main
        ;;
esac
