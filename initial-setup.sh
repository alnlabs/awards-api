#!/bin/bash
set -e

COMPOSE_FILE="docker-compose.dev.yml"
DB_USER="awards_user"

echo "🚀 Initial setup starting..."

# Step 1: Init environment
./init.sh

# Step 2: Start containers
./docker.sh start

# Step 3: Wait for DB to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker compose -f $COMPOSE_FILE exec -T db pg_isready -U $DB_USER > /dev/null 2>&1; do
  sleep 1
done
echo "✅ Database is ready"

# Step 4: Run migrations
./docker.sh migrate-up

# Step 5: Seed admin user
./test.sh seed

echo ""
echo "✅ Initial setup completed successfully!"
echo "📘 API Docs: http://localhost:4100/docs"