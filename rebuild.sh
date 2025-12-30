#!/bin/bash
set -e

COMPOSE_FILE="docker-compose.dev.yml"
DB_USER="awards_user"

echo "🔄 Rebuilding environment (FORCED clean)..."

# --------------------------------------------------
# Step 1: Force stop & remove everything (NO PROMPT)
# --------------------------------------------------
echo "🧹 Removing containers, images & volumes..."
docker compose -f $COMPOSE_FILE down -v --remove-orphans

# --------------------------------------------------
# Step 2: Build & start fresh containers
# --------------------------------------------------
echo "🚀 Building & starting containers..."
docker compose -f $COMPOSE_FILE up --build -d

# --------------------------------------------------
# Step 3: Wait for PostgreSQL
# --------------------------------------------------
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker compose -f $COMPOSE_FILE exec -T db pg_isready -U $DB_USER > /dev/null 2>&1; do
  sleep 1
done
echo "✅ Database is ready"

# --------------------------------------------------
# Step 4: Run migrations
# --------------------------------------------------
echo "⬆️  Running migrations..."
docker compose -f $COMPOSE_FILE exec -T api alembic upgrade head

# --------------------------------------------------
# Step 5: Seed data
# --------------------------------------------------
echo "🌱 Seeding database..."
./docker.sh seed

echo ""
echo "✅ Rebuild completed successfully!"