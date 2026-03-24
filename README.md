# Employee Awards API

Internal system to manage employee awards and nominations.

## 🚀 Quick Start & Lifecycle

Manage the entire system lifecycle using the following workflows.

### 1. First-Time Setup (Fresh Install)
Get the system up and running from scratch.
```bash
./init.sh              # 1. Initialize environment & .env
./docker.sh start      # 2. Start containers
./docker.sh initial-config # 3. Full baseline setup (SUPER_ADMIN only)
```
> **Default Admin**: `admin@company.com` / `ChangeMe123`

---

### 2. Daily Operations (Continuing Work)
Resume development or production service.
```bash
./docker.sh start      # 1. Start containers
./docker.sh migrate-up # 2. Apply any new database changes
```

---

### 3. Backup & Restore (Data Management)
Safeguard or migrate your data.
```bash
./docker.sh backup-db            # Create timestamped SQL dump
./docker.sh import-db <dump_path> # Restore from a specific snapshot
```

---

### 4. System Reset (Wipe & Restart)
Completely clear all data and start fresh.
```bash
./docker.sh reset      # ⚠️ Deletes ALL containers, volumes, and data
./docker.sh start
./docker.sh initial-config
```

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

Manages Docker containers, database migrations, and **time-based backups**.

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
- `./docker.sh initial-config` - Full initial configuration (**SUPER\_ADMIN only**)

**Database Backups:**
- `./docker.sh backup-db` - Create a timestamped SQL dump in `./backups/YYYYMMDD-HHMMSS/`
- `./docker.sh import-db <path>` - Restore database from a SQL snapshot

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

1. **Environmental Initialization**:
   Use `./init.sh` to ensure your `.env` and dependencies are ready.

2. **Database Management**:
   Always run `./docker.sh migrate-up` after pulling new changes to ensure your schema is in sync. Use `./docker.sh migrate-create 'msg'` for new changes.

3. **Baseline Data**:
   Use `./docker.sh initial-config` for a production-ready baseline, or `./docker.sh mock-seed` for a development environment with sample records.

4. **Testing**:
   Run `./test.sh all` before submitting pull requests. Use `./test.sh coverage` to check test density.

## ⚙️ Environment Variables

The application is configured via environment variables. Copy `.env.example` to `.env` to get started:

```bash
cp .env.example .env
```

### Required & Optional Variables

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | String | `dev` | System environment: `local`, `dev`, or `prod`. |
| `API_PORT` | Integer | `4100` | The host port the API will listen on. |
| `DB_PORT` | Integer | `5433` | The host port the Database will listen on. |
| `DATABASE_URL` | String | - | Connection string for PostgreSQL. |
| `JWT_SECRET` | String | - | **CRITICAL**: Secure random string for JWT signing. |
| `BACKEND_CORS_ORIGINS` | String | - | Comma-separated list of allowed frontend URLs. |

---

## 🏗️ Multi-Environment Support

The system supports separate configurations for different stages of the lifecycle:

### 1. Local / Development
Optimized for rapid iteration with hot-reloading enabled.
- **Config**: `APP_ENV=local` or `dev`
- **Command**: `./docker.sh start` (uses `docker-compose.dev.yml`)

### 2. Production
Optimized for stability and performance.
- **Config**: `APP_ENV=prod`, `API_PORT=80`
- **Command**: 
  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  ```

---

## 🔌 Port Control

If you encounter port conflicts (e.g., port 4100 is in use), simply update your `.env` file:

1. Open `.env`
2. Change `API_PORT=4101`
3. Restart the system: `./docker.sh restart`

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
./docker.sh start
./docker.sh initial-config
```

## Additional Resources

- [API Documentation](DOCS.md) - Full API implementation documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/) - FastAPI framework documentation
- [Alembic Docs](https://alembic.sqlalchemy.org/) - Database migration tool documentation
