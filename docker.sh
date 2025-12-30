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
  echo "  reset           Stop & remove containers + volumes (⚠️ deletes data)"
  echo ""
  echo "Database migrations:"
  echo "  migrate-create  Create new migration (requires message)"
  echo "  migrate-up      Run all pending migrations"
  echo "  migrate-down    Rollback last migration"
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

  *)
    print_help
    ;;
esac

