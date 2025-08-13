#!/usr/bin/env bash

# Config
CONTAINER_NAME="openfpa_postgres"
DB_USER="root"
DB_NAME="openfpa_db"

# Run table list command inside container
docker exec -it "$CONTAINER_NAME" \
  psql -U "$DB_USER" -d "$DB_NAME" -c "\dt"

