# admin-law-review — Multi-stage Docker build
# ==============================================
# Stage 1: Install dependencies (cached layer)
FROM python:3.11-slim AS deps

WORKDIR /install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r reviewer && useradd -r -g reviewer -d /app -s /sbin/nologin reviewer

WORKDIR /app

# Copy installed dependencies from build stage
COPY --from=deps /install/deps /usr/local

# Copy application code
COPY main.py .
COPY backend/ backend/
COPY frontend/ frontend/

# Ensure database directory is writable
RUN mkdir -p /app/data && chown -R reviewer:reviewer /app

# Environment configuration
ENV PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1 \
    ADMIN_LAW_DB_PATH="/app/data/admin_law_review.db"

EXPOSE 8000

USER reviewer

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
