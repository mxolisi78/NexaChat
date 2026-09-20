# ─────────────────────────────────────────────────────────────
# NexaChat — Production Docker image
# ─────────────────────────────────────────────────────────────
FROM python:3.13-slim

# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps needed by psycopg, Pillow, and Daphne
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the project
COPY . .

# Collect static files (Whitenoise will serve them)
RUN python manage.py collectstatic --noinput || true

# Non-root user for security
RUN useradd -m -u 1000 nexachat && chown -R nexachat:nexachat /app
USER nexachat

EXPOSE 8000

# Healthcheck — useful for orchestration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/ || exit 1

# Daphne serves HTTP + WebSocket via ASGI
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "nexachat.asgi:application"]