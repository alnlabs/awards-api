# Employee Awards API

Internal system to manage employee awards and nominations.

## Quick Start

### 1. Initial Setup

```bash
# Run setup script
./init.sh

# Or with virtual environment
./init.sh --venv
```

### 2. Start Development Environment

```bash
# Start containers
./docker.sh start

# Stop containers
./docker.sh stop
```

### 3. Initialize Database

```bash
# Run migrations
./docker.sh migrate-up

# Create admin user (optional - also created automatically on API startup)
./test.sh seed
```

**Admin User Credentials:**
- Email: `admin@company.com`
- Password: `ChangeMe123`
- Role: `HR`

> **Note:** The admin user is automatically created when the API starts. Use `./test.sh seed` to create it manually after initialization.

## Available Scripts

### `init.sh` - Initial Setup

Sets up the development environment:
- Creates `.env` file from `.env.example`
- Optionally creates Python virtual environment
- Checks Docker installation
- Creates necessary directories

**Usage:**
```bash
./init.sh              # Basic setup
./init.sh --venv       # Setup with virtual environment
```

### `docker.sh` - Docker Container Management

Manages Docker containers and database migrations.

**Container Commands:**
- `./docker.sh start` - Start containers (background)
- `./docker.sh stop` - Stop containers
- `./docker.sh restart` - Restart containers
- `./docker.sh logs` - View API logs
- `./docker.sh status` - Show running containers
- `./docker.sh reset` - ⚠️ Stop & remove containers + volumes (deletes data)

**Migration Commands:**
- `./docker.sh migrate-create 'message'` - Create new migration
- `./docker.sh migrate-up` - Run all pending migrations
- `./docker.sh migrate-down` - Rollback last migration

**Examples:**
```bash
./docker.sh start                        # Start containers
./docker.sh logs                         # View logs
./docker.sh migrate-create 'add user table'
./docker.sh migrate-up
./docker.sh migrate-down
```

### `test.sh` - Testing & Development Tools

Testing, development utilities, and helpers.

**Testing:**
- `./test.sh all` - Run all tests
- `./test.sh coverage` - Run tests with coverage
- `./test.sh unit` - Run unit tests only
- `./test.sh integration` - Run integration tests only

**Development Tools:**
- `./test.sh shell` - Open shell in API container
- `./test.sh db-shell` - Open PostgreSQL shell
- `./test.sh lint` - Run linters
- `./test.sh format` - Format code

**Database:**
- `./test.sh init` - Initialize database (run migrations)
- `./test.sh seed` - Create admin user (admin@company.com / ChangeMe123)

**Note:** The admin user is also created automatically when the API starts. Use `./test.sh seed` to create it manually after initialization.

**Utilities:**
- `./test.sh status` - Show environment status
- `./test.sh clean` - Clean up Docker resources

**Examples:**
```bash
./test.sh all          # Run all tests
./test.sh shell        # Access API container
./test.sh db-shell     # Access database
./test.sh status       # Check environment status
./test.sh seed         # Create admin user
```

## Development Workflow

1. **Initial Setup:**
   ```bash
   ./init.sh
   ```

2. **Start Development:**
   ```bash
   ./docker.sh start
   ```

3. **Database Migrations:**
   ```bash
   # Create migration after model changes
   ./docker.sh migrate-create 'description of changes'

   # Apply migrations
   ./docker.sh migrate-up

   # Rollback if needed
   ./docker.sh migrate-down
   ```

4. **Testing & Development:**
   ```bash
   ./test.sh all         # Run all tests
   ./test.sh shell       # Debug in container
   ./test.sh status      # Check system status
   ```

5. **Seed Admin User (Optional):**
   ```bash
   ./test.sh seed        # Create admin user (admin@company.com / ChangeMe123)
   ```
   Note: Admin user is also created automatically when the API starts. Run this separately if you need to create it after initialization.

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

## API Documentation

Once the server is running:
- **Swagger UI**: http://localhost:4100/docs
- **ReDoc**: http://localhost:4100/redoc
- **Health Check**: http://localhost:4100/api/v1/health

## Project Structure

```
employee-awards-api/
├── app/                 # Application code
│   ├── api/            # API routes
│   ├── core/           # Core utilities
│   ├── models/         # Database models
│   └── schemas/        # Pydantic schemas
├── alembic/            # Database migrations
├── docker/             # Dockerfiles
├── docker.sh           # Docker container management
├── test.sh             # Testing & development tools
├── init.sh             # Initial setup
└── docker-compose.dev.yml
```

## Troubleshooting

**Database connection issues:**
```bash
./test.sh status        # Check container status
./docker.sh restart     # Restart containers
```

**Reset everything:**
```bash
./docker.sh reset       # WARNING: Deletes all data
./init.sh               # Re-run setup
./test.sh init          # Reinitialize database
```

## Additional Resources

- [API Documentation](DOCS.md) - Full API implementation documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/) - FastAPI framework documentation
- [Alembic Docs](https://alembic.sqlalchemy.org/) - Database migration tool documentation
