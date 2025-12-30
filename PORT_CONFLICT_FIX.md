# Port Conflict Fix

## Issue
Port 5432 is already in use by another PostgreSQL instance on your machine.

## Solution Applied
The docker-compose file has been updated to use port **5433** instead of 5432 for the database container.

## What Changed
- Database container now maps to port **5433** on your host machine
- Internal container port remains **5432** (unchanged)
- Connection string in `.env` should use `db:5432` (container name) - this is correct

## If You Need to Use Port 5432

### Option 1: Stop Local PostgreSQL (macOS)
```bash
# Stop PostgreSQL if installed via Homebrew
brew services stop postgresql@15
# or
brew services stop postgresql@14
# or
brew services stop postgresql

# Check what's running
brew services list
```

### Option 2: Stop Local PostgreSQL (Linux)
```bash
# Stop PostgreSQL service
sudo systemctl stop postgresql
# or
sudo service postgresql stop
```

### Option 3: Change Back to Port 5432
If you've stopped the local PostgreSQL, you can change the port back:
```yaml
ports:
  - "5432:5432"
```

## Connecting to the Database

### From Host Machine (if needed)
```bash
# Using psql
psql -h localhost -p 5433 -U awards_user -d awards_db

# Or using docker
docker exec -it awards_db_dev psql -U awards_user -d awards_db
```

### From Application
The application uses the container name `db` and internal port `5432`:
```
DATABASE_URL=postgresql+psycopg2://awards_user:awards_pass@db:5432/awards_db
```
This is correct and doesn't need to change.

## Verify Port is Available
```bash
# Check if port 5433 is available
lsof -i :5433

# Or check what's using 5432
lsof -i :5432
```

