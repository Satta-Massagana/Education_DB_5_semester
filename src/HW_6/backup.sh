#!/bin/bash
BACKUP_ROOT="/backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)

echo "Starting backup $DATE..."

# PostgreSQL
docker exec postgres pg_dump -U postgres postgres | gzip > $BACKUP_ROOT/postgres_$DATE.sql.gz

# Redis
docker exec redis bash -c "echo 'SAVE' | redis-cli" && \
docker cp postgres:/var/lib/redis/dump.rdb $BACKUP_ROOT/redis_$DATE.rdb

echo "All backups created in $BACKUP_ROOT"
