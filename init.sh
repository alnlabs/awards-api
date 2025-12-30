#!/bin/bash

set -e

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

# Optional: Create Python virtual environment
if [ "$1" == "--venv" ]; then
  if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo "💡 Activate with: source venv/bin/activate"
  else
    echo "ℹ️  Virtual environment already exists"
  fi
fi

# Check Docker installation
if ! command -v docker &> /dev/null; then
  echo "❌ Docker is not installed. Please install Docker first."
  exit 1
fi

if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
  echo "❌ Docker Compose is not installed. Please install Docker Compose first."
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

echo ""
echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "  1. Review .env file"
echo "  2. Start containers: ./docker.sh start"
echo "  3. Run migrations: ./docker.sh migrate-up"
echo "  4. Access API docs: http://localhost:4100/docs"
echo ""

