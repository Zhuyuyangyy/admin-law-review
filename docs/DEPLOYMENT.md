# Deployment Guide

## Prerequisites

- Python 3.11+
- Docker (optional)
- 512MB+ RAM
- 1GB+ disk space

## Local Development

### 1. Clone and Setup

```bash
git clone https://github.com/<your-org>/admin-law-review.git
cd admin-law-review
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Run Backend

```bash
# Option 1: Direct run
python main.py

# Option 2: With uvicorn
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Option 3: With gunicorn (production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 3. Run Frontend

Open `frontend/index.html` in a browser.

### 4. Access API

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Docker Deployment

### Build Image

```bash
docker build -t admin-law-review .
```

### Run Container

```bash
docker run -d \
  --name admin-law-review \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  admin-law-review
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_LAW_DB_PATH` | `/app/data/admin_law_review.db` | SQLite database path |
| `PYTHONPATH` | `/app/backend` | Python module path |
| `PYTHONUNBUFFERED` | `1` | Disable Python output buffering |

## Production Considerations

### 1. Database

- SQLite works for single-instance deployments
- For multi-instance, consider PostgreSQL or MySQL
- Regular backups of the database file

### 2. Security

- Restrict CORS origins in production
- Add authentication/authorization
- Use HTTPS with reverse proxy (nginx/caddy)
- Rotate audit logs

### 3. Monitoring

- Health check endpoint: `/health`
- Docker healthcheck configured (30s interval)
- Monitor disk space for database growth

### 4. Scaling

- Horizontal scaling requires shared database
- Consider Redis for caching
- Use message queue for async processing

### 5. Backup

```bash
# Backup database
cp admin_law_review.db backup_$(date +%Y%m%d).db

# Backup with Docker
docker exec admin-law-review cat /app/data/admin_law_review.db > backup.db
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows
```

### Database Locked

```bash
# Check for lock files
ls -la *.db*

# Remove lock if stale
rm -f admin_law_review.db-journal
```

### Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/path/to/admin-law-review/backend

# Or run from project root
cd admin-law-review
python main.py
```

## CI/CD Pipeline

The project uses GitHub Actions for CI/CD:

1. **Lint**: ruff check for code quality
2. **Test**: pytest for unit and integration tests
3. **Docker**: Build and verify container (main branch only)

### Manual CI Run

```bash
# Lint
pip install ruff
ruff check backend/ tests/

# Test
pytest tests/ -v --cov=backend/app --cov-report=term-missing

# Docker
docker build -t admin-law-review .
docker run -d --name test -p 8000:8000 admin-law-review
curl -f http://localhost:8000/health
docker stop test
```
