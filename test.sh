#!/bin/bash

set -e

COMPOSE_FILE="docker-compose.dev.yml"

print_help() {
  echo ""
  echo "Usage: ./test.sh [command]"
  echo ""
  echo "Testing:"
  echo "  all             Run all tests"
  echo "  coverage        Run tests with coverage report"
  echo "  unit            Run unit tests only"
  echo "  integration     Run integration tests only"
  echo ""
  echo "Development tools:"
  echo "  shell           Open shell in API container"
  echo "  db-shell        Open PostgreSQL shell"
  echo "  lint            Run linters"
  echo "  format          Format code"
  echo ""
  echo "Database:"
  echo "  init            Initialize database (run migrations)"
  echo "  seed            Create admin user (admin@company.com / ChangeMe123)"
  echo ""
  echo "Utilities:"
  echo "  status          Show environment status"
  echo "  clean           Clean up Docker resources"
  echo ""
}

case "$1" in
  all)
    echo "🧪 Running all tests..."
    docker compose -f $COMPOSE_FILE build api > /dev/null 2>&1
    docker compose -f $COMPOSE_FILE run --rm api python -m pytest tests/ -v
    ;;

  coverage)
    echo "🧪 Running tests with coverage..."
    docker compose -f $COMPOSE_FILE build api > /dev/null 2>&1
    docker compose -f $COMPOSE_FILE run --rm api python -m pytest tests/ -v --cov=app --cov-report=term-missing
    ;;

  unit)
    echo "🧪 Running unit tests..."
    docker compose -f $COMPOSE_FILE build api > /dev/null 2>&1
    docker compose -f $COMPOSE_FILE run --rm api python -m pytest tests/ -v -m unit
    ;;

  integration)
    echo "🧪 Running integration tests..."
    docker compose -f $COMPOSE_FILE build api > /dev/null 2>&1
    docker compose -f $COMPOSE_FILE run --rm api python -m pytest tests/ -v -m integration
    ;;

  shell)
    echo "🐚 Opening shell in API container..."
    docker compose -f $COMPOSE_FILE exec api /bin/bash || \
    docker compose -f $COMPOSE_FILE run --rm api /bin/bash
    ;;

  db-shell)
    echo "🗄️  Opening PostgreSQL shell..."
    docker compose -f $COMPOSE_FILE exec db psql -U awards_user -d awards_db
    ;;

  lint)
    echo "🔍 Running linters..."
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api python -m flake8 app 2>/dev/null || \
      docker compose -f $COMPOSE_FILE exec api python -m pylint app 2>/dev/null || \
      echo "ℹ️  No linter configured"
    else
      docker compose -f $COMPOSE_FILE run --rm api python -m flake8 app 2>/dev/null || \
      docker compose -f $COMPOSE_FILE run --rm api python -m pylint app 2>/dev/null || \
      echo "ℹ️  No linter configured"
    fi
    ;;

  format)
    echo "💅 Formatting code..."
    if docker compose -f $COMPOSE_FILE ps api | grep -q "Up"; then
      docker compose -f $COMPOSE_FILE exec api python -m black app 2>/dev/null || \
      echo "ℹ️  black not installed. Install with: pip install black"
    else
      docker compose -f $COMPOSE_FILE run --rm api python -m black app 2>/dev/null || \
      echo "ℹ️  black not installed. Install with: pip install black"
    fi
    ;;

  init)
    echo "🚀 Initializing database..."
    docker compose -f $COMPOSE_FILE up -d db
    sleep 5
    docker compose -f $COMPOSE_FILE run --rm api alembic upgrade head
    echo "✅ Database initialized"
    ;;

  seed)
    echo "🌱 Seeding admin user..."
    echo "📧 Email: admin@company.com"
    echo "🔑 Password: ChangeMe123"
    echo ""
    docker compose -f $COMPOSE_FILE run --rm api python -c "
from app.core.database import SessionLocal
from app.core.seed import seed_admin_user
db = SessionLocal()
try:
    seed_admin_user(db)
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
finally:
    db.close()
"
    echo ""
    echo "✅ Seed completed"
    echo "⚠️  Remember to change the password after first login!"
    ;;

  status)
    echo "📊 Environment Status"
    echo "===================="
    echo ""
    echo "Containers:"
    docker compose -f $COMPOSE_FILE ps
    echo ""
    echo "Database:"
    docker compose -f $COMPOSE_FILE exec -T db pg_isready -U awards_user 2>/dev/null && \
      echo "✅ Ready" || echo "❌ Not ready"
    echo ""
    echo "API:"
    curl -s http://localhost:4100/api/v1/health 2>/dev/null && \
      echo "✅ Responding" || echo "❌ Not responding"
    echo ""
    ;;

  clean)
    echo "🧹 Cleaning up Docker resources..."
    echo "⚠️  This will remove containers, volumes, and images"
    read -p "Continue? (y/N): " CONFIRM
    if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
      docker compose -f $COMPOSE_FILE down -v --rmi local
      echo "✅ Cleanup completed"
    else
      echo "❌ Cancelled"
    fi
    ;;

  *)
    print_help
    ;;
esac

