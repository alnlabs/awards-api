#!/bin/bash

set -e

# ---- Load Environment Variables ----
if [ -f .env ]; then
  # Load .env variables and export them
  export $(grep -v '^#' .env | xargs)
else
  echo "⚠️  Warning: .env file not found. Using defaults."
fi

# Set compose file based on APP_ENV
if [ "$APP_ENV" = "prod" ]; then
  COMPOSE_FILE="docker-compose.prod.yml"
else
  COMPOSE_FILE="docker-compose.dev.yml"
fi

echo "🌍 Environment: ${APP_ENV:-dev} (using $COMPOSE_FILE)"

# ---- Validation Helpers ----

check_db_ready() {
  if ! docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
    echo "❌ Error: Database container is not running."
    echo "💡 Run './docker.sh start' first."
    return 1
  fi
  
  if ! docker compose -f $COMPOSE_FILE exec -T db pg_isready -U awards_user >/dev/null 2>&1; then
    echo "⏳ Waiting for database to be ready..."
    sleep 3
    if ! docker compose -f $COMPOSE_FILE exec -T db pg_isready -U awards_user >/dev/null 2>&1; then
      echo "❌ Error: Database is not responding."
      return 1
    fi
  fi
  return 0
}

check_migrations_applied() {
  if ! docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      echo "❌ Error: API container is not running."
      return 1
  fi
  
  # Check if migrations are current
  STATUS=$(docker compose -f $COMPOSE_FILE exec -T api alembic current 2>&1)
  if [[ $STATUS == *"(head)"* ]]; then
    return 0
  else
    echo "⚠️  Warning: Database migrations are not up to date."
    echo "💡 Run './docker.sh migrate-up' before proceeding."
    return 1
  fi
}

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
  echo "  init            Initial environment setup (.env, directories, etc.)"
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
  echo "  initial-config  Full initial configuration (SUPER_ADMIN only)"
  echo ""
  echo "Database backups:"
  echo "  backup-db       Create a timestamped DB backup in ./backups"
  echo "  import-db       Import a DB backup (requires path to .sql file)"
  echo ""
  echo "Examples:"
  echo "  ./docker.sh start"
  echo "  ./docker.sh migrate-create 'add user table'"
  echo "  ./docker.sh migrate-up"
  echo ""
}

case "$1" in
  init)
    echo "🚀 Setting up development environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
      echo "📝 Creating .env file..."
      if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env file created from .env.example"
      else
        cat > .env <<EOF
DATABASE_URL=postgresql+psycopg2://awards_user:awards_pass@db:5432/awards_db
JWT_SECRET=dev_secret_change_later
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
EOF
        echo "✅ Default .env file created"
      fi
    else
      echo "ℹ️  .env file already exists"
    fi

    # Check Docker installation
    if ! command -v docker &> /dev/null; then
      echo "❌ Docker is not installed. Please install Docker first."
      exit 1
    fi
    echo "✅ Docker installed"

    # Create alembic versions directory
    if [ ! -d "alembic/versions" ]; then
      echo "📁 Creating alembic/versions directory..."
      mkdir -p alembic/versions
      touch alembic/versions/.gitkeep
      echo "✅ Directory created"
    fi

    # Make scripts executable
    chmod +x docker.sh test.sh init.sh 2>/dev/null || true
    echo "✅ Scripts made executable"

    echo ""
    echo "✅ Setup completed!"
    echo "💡 Next: ./docker.sh start"
    ;;

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
    check_db_ready || exit 1

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
    check_db_ready || exit 1

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
    check_db_ready || exit 1

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
    check_db_ready || exit 1

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

  initial-config)
    echo "🏗️  Setting up full initial configuration..."
    check_db_ready || exit 1

    # Interactive Prompts
    echo ""
    echo "📋 Please provide the following details for initial setup:"
    read -p "🏢 Company Name [Employee Awards Platform]: " COMPANY_NAME
    read -p "📧 Admin Email [admin@company.com]: " ADMIN_EMAIL
    read -s -p "🔑 Admin Password [ChangeMe123]: " ADMIN_PASSWORD
    echo ""
    echo "🛡️  Set answers for the 3 default security questions:"
    read -p "1. What is your pet's name? " ANS1
    read -p "2. What city were you born in? " ANS2
    read -p "3. What is your favorite color? " ANS3
    echo ""

    # Ensure migrations are up to date
    echo "⬆️  Ensuring migrations are up to date..."
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api alembic upgrade head
    else
      docker compose -f $COMPOSE_FILE run --rm api alembic upgrade head
    fi

    # Prepare arguments
    ARGS=""
    [ -n "$COMPANY_NAME" ] && ARGS="$ARGS --company \"$COMPANY_NAME\""
    [ -n "$ADMIN_EMAIL" ] && ARGS="$ARGS --email \"$ADMIN_EMAIL\""
    [ -n "$ADMIN_PASSWORD" ] && ARGS="$ARGS --password \"$ADMIN_PASSWORD\""
    [ -n "$ANS1" ] && [ -n "$ANS2" ] && [ -n "$ANS3" ] && ARGS="$ARGS --answers \"$ANS1\" \"$ANS2\" \"$ANS3\""

    # Run the initial setup script
    echo "📝 Running initial setup script..."
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      # Use sh -c to handle quoted arguments correctly in exec
      docker compose -f $COMPOSE_FILE exec api sh -c "python -m app.seeds.initial_setup $ARGS"
    else
      docker compose -f $COMPOSE_FILE run --rm api sh -c "python -m app.seeds.initial_setup $ARGS"
    fi

    echo "✅ Full initial configuration completed"
    ;;

  backup-db)
    echo "💾 Creating database backup..."
    check_db_ready || exit 1

    TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
    BACKUP_DIR="backups/$TIMESTAMP"
    mkdir -p "$BACKUP_DIR"
    FILE_NAME="$BACKUP_DIR/db-backup.sql"

    echo "📁 Writing backup to: $FILE_NAME"
    docker compose -f $COMPOSE_FILE exec -T db pg_dump -U awards_user -d awards_db > "$FILE_NAME"
    echo "✅ Backup completed"
    ;;

  import-db)
    if [ -z "$2" ]; then
      echo "❌ Error: Backup file path is required"
      echo "Usage: ./docker.sh import-db backups/YYYYMMDD-HHMMSS/db-backup.sql"
      exit 1
    fi

    if [ ! -f "$2" ]; then
      echo "❌ Error: File not found: $2"
      exit 1
    fi

    echo "⚠️  WARNING: This will overwrite existing data!"
    read -p "Type YES to continue: " CONFIRM
    if [ "$CONFIRM" = "YES" ]; then
      # Ensure database is running
      if ! docker compose -f $COMPOSE_FILE ps db | grep -q "Up"; then
        echo "Starting database..."
        docker compose -f $COMPOSE_FILE up -d db
        echo "Waiting for database to be ready..."
        sleep 5
      fi

      echo "📥 Importing backup from: $2"
      # Use cat and pipe to docker exec to handle files outside the container
      cat "$2" | docker compose -f $COMPOSE_FILE exec -T db psql -U awards_user -d awards_db
      echo "✅ Import completed"
    else
      echo "❌ Import cancelled"
    fi
    ;;

  *)
    print_help
    ;;
esac

