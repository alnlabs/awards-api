#!/bin/bash

set -e

COMPOSE_FILE="docker-compose.dev.yml"

print_help() {
  echo ""
  echo "Usage: ./docker.sh [command]"
  echo ""
  echo "Docker container management:"
  echo "  start           Start containers (background)"
  echo "  stop            Stop containers"
  echo "  restart         Restart containers"
  echo "  logs            View API logs"
  echo "  status          Show running containers"
  echo "  db-status       Check database & API health"
  echo "  reset           Stop & remove containers + volumes (⚠️ deletes data)"
  echo ""
  echo "Database migrations:"
  echo "  migrate-create  Create new migration (requires message)"
  echo "  migrate-up      Run all pending migrations"
  echo "  migrate-down    Rollback last migration"
  echo "  migrate-status  Show current migration status"
  echo ""
  echo "Database seeding:"
  echo "  seed            Seed REAL baseline data (SUPER_ADMIN only)"
  echo "  mock-seed       Seed MOCK data (SUPER_ADMIN + sample users)"
  echo ""
  echo "Database backups:"
  echo "  backup-db       Create a timestamped DB backup in ./backups"
  echo ""
  echo "Examples:"
  echo "  ./docker.sh start"
  echo "  ./docker.sh migrate-create 'add user table'"
  echo "  ./docker.sh migrate-up"
  echo ""
}

case "$1" in
  start)
    echo "🚀 Starting containers..."
    docker compose -f $COMPOSE_FILE up --build -d
    echo "✅ Containers started in background"
    echo "💡 Use './docker.sh logs' to view logs or './docker.sh status' to check status"
    ;;

  stop)
    echo "🛑 Stopping containers..."
    docker compose -f $COMPOSE_FILE down
    echo "✅ Containers stopped"
    ;;

  restart)
    echo "🔄 Restarting containers..."
    docker compose -f $COMPOSE_FILE down
    docker compose -f $COMPOSE_FILE up --build -d
    echo "✅ Containers restarted"
    ;;

  logs)
    echo "📜 Showing API logs..."
    docker compose -f $COMPOSE_FILE logs -f api
    ;;

  status)
    docker compose -f $COMPOSE_FILE ps
    ;;

  db-status)
    echo "📊 Environment Status"
    echo "===================="
    echo ""
    echo "Containers:"
    docker compose -f $COMPOSE_FILE ps
    echo ""
    echo "Database:"
    # Use pg_isready inside db container if it's running
    if docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec -T db pg_isready -U awards_user 2>/dev/null && \
        echo "✅ Ready" || echo "❌ Not ready"
      # DB stats (size + table row counts)
      echo ""
      echo "DB Stats:"
      docker compose -f $COMPOSE_FILE exec -T db psql -U awards_user -d awards_db -t -A 2>/dev/null <<'EOSQL' | while read -r line; do echo "  $line"; done
SELECT 'Database size: ' || pg_size_pretty(pg_database_size('awards_db'));
SELECT relname || ': ' || n_live_tup FROM pg_stat_user_tables WHERE schemaname = 'public' ORDER BY relname;
EOSQL
    else
      echo "❌ DB container not running"
    fi
    echo ""
    echo "API:"
    # Check FastAPI health endpoint if API container is up
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      curl -s http://localhost:4100/api/v1/health 2>/dev/null && \
        echo " ✅ Responding" || echo " ❌ Not responding"
    else
      echo "❌ API container not running"
    fi
    echo ""
    ;;

  reset)
    echo "⚠️  WARNING: This will delete all data!"
    read -p "Type YES to continue: " CONFIRM
    if [ "$CONFIRM" = "YES" ]; then
      docker compose -f $COMPOSE_FILE down -v
      echo "✅ Containers and volumes removed"
    else
      echo "❌ Reset cancelled"
    fi
    ;;

  migrate-create)
    if [ -z "$2" ]; then
      echo "❌ Error: Migration message is required"
      echo "Usage: ./docker.sh migrate-create 'your migration message'"
      exit 1
    fi
    echo "📝 Creating migration: $2"
    # Ensure database is running
    if ! docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
      echo "Starting database..."
      docker compose -f $COMPOSE_FILE up -d db
      echo "Waiting for database to be ready..."
      sleep 5
    fi

    # Try to run migration in existing container, otherwise create new one
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api alembic revision --autogenerate -m "$2"
    else
      docker compose -f $COMPOSE_FILE run --rm api alembic revision --autogenerate -m "$2"
    fi
    echo "✅ Migration created"
    ;;

  migrate-up)
    echo "⬆️  Running migrations..."
    # Ensure database is running
    if ! docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
      echo "Starting database..."
      docker compose -f $COMPOSE_FILE up -d db
      echo "Waiting for database to be ready..."
      sleep 5
    fi

    # Check current migration state first
    echo "📊 Current migration state:"
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api alembic current
    else
      docker compose -f $COMPOSE_FILE run --rm api alembic current
    fi
    echo ""
    
    # Try to run migration in existing container, otherwise create new one
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api alembic upgrade head
    else
      docker compose -f $COMPOSE_FILE run --rm api alembic upgrade head
    fi
    echo "✅ Migrations completed"
    ;;

  migrate-down)
    echo "⬇️  Rolling back last migration..."
    # Ensure database is running
    if ! docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
      echo "Starting database..."
      docker compose -f $COMPOSE_FILE up -d db
      echo "Waiting for database to be ready..."
      sleep 5
    fi

    # Try to run migration in existing container, otherwise create new one
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api alembic downgrade -1
    else
      docker compose -f $COMPOSE_FILE run --rm api alembic downgrade -1
    fi
    echo "✅ Migration rolled back"
    ;;

  migrate-status)
    echo "📊 Migration Status:"
    # Ensure database is running
    if ! docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
      echo "Starting database..."
      docker compose -f $COMPOSE_FILE up -d db
      echo "Waiting for database to be ready..."
      sleep 5
    fi

    echo ""
    echo "Current migration:"
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api alembic current
    else
      docker compose -f $COMPOSE_FILE run --rm api alembic current
    fi
    
    echo ""
    echo "Migration history:"
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api alembic history
    else
      docker compose -f $COMPOSE_FILE run --rm api alembic history
    fi
    ;;

  seed)
    echo "🌱 Seeding REAL baseline data..."
    # Ensure database is running
    if ! docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
      echo "Starting database..."
      docker compose -f $COMPOSE_FILE up -d db
      echo "Waiting for database to be ready..."
      sleep 5
    fi

    # Ensure migrations are up to date before seeding
    echo "⬆️  Ensuring migrations are up to date..."
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api alembic upgrade head
    else
      docker compose -f $COMPOSE_FILE run --rm api alembic upgrade head
    fi

    # Run the real seed script
    echo "📝 Running real seed script..."
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api python real-seeds.py
    else
      docker compose -f $COMPOSE_FILE run --rm api python real-seeds.py
    fi

    echo "✅ Seeding completed"
    ;;

  mock-seed)
    echo "🌱 Seeding MOCK data (SUPER_ADMIN + sample users)..."
    # Ensure database is running
    if ! docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
      echo "Starting database..."
      docker compose -f $COMPOSE_FILE up -d db
      echo "Waiting for database to be ready..."
      sleep 5
    fi

    # Ensure migrations are up to date before seeding
    echo "⬆️  Ensuring migrations are up to date..."
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api alembic upgrade head
    else
      docker compose -f $COMPOSE_FILE run --rm api alembic upgrade head
    fi

    # Run the mock seed script
    echo "📝 Running mock seed script..."
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api python mock-seeds.py
    else
      docker compose -f $COMPOSE_FILE run --rm api python mock-seeds.py
    fi

    echo "✅ Mock seeding completed"
    ;;

  backup-db)
    echo "💾 Creating database backup..."
    # Ensure database is running
    if ! docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
      echo "Starting database..."
      docker compose -f $COMPOSE_FILE up -d db
      echo "Waiting for database to be ready..."
      sleep 5
    fi

    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
    FILE_NAME="$BACKUP_DIR/db-backup-$TIMESTAMP.sql"

    echo "📁 Writing backup to: $FILE_NAME"
    docker compose -f $COMPOSE_FILE exec -T db pg_dump -U awards_user -d awards_db > "$FILE_NAME"
    echo "✅ Backup completed"
    ;;

  *)
    print_help
    ;;
esac

