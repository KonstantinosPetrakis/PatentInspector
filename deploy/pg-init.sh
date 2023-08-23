#!/bin/bash
echo "Installing extensions for Postgres..."
psql -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE EXTENSION pg_trgm;"

echo "Downloading backup..."
cd ~
python3 /backup_helper.py $POSTGRES_DB $DOWNLOAD_BACKUP_URL1 $DOWNLOAD_BACKUP_URL2
