# ─── Base image ───────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ─── Environment ──────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ─── Working directory ────────────────────────────────────────────────────────
WORKDIR /app

# ─── Install system dependencies ──────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ─── Install Python dependencies ──────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Copy application source ───────────────────────────────────────────────────
COPY . .

# ─── Make entrypoint executable ───────────────────────────────────────────────
RUN chmod +x entrypoint.sh

# ─── Expose port ──────────────────────────────────────────────────────────────
EXPOSE 8000

# ─── Run server ───────────────────────────────────────────────────────────────
# Railway provides PORT env variable, default to 8000 for local development
ENTRYPOINT ["./entrypoint.sh"]
