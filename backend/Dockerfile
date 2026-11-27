# Build context: repo root (needs data/seed). See docker-compose.yml.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv/backend

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY data/seed /srv/data/seed

# Non-root; /data holds the SQLite file on a named volume.
RUN useradd --system --uid 10001 app && mkdir /data && chown app /data
USER app

ENV DATABASE_URL=sqlite:////data/autocare.db
EXPOSE 8000

# Seed is idempotent and validates first: a bad seed stops the container instead of serving it.
CMD ["sh", "-c", "python -m app.seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
