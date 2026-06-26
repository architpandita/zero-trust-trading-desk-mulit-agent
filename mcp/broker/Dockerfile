# syntax=docker/dockerfile:1.4
FROM python:3.11-slim AS base

WORKDIR /app

# --- deps layer (cached unless requirements.txt changes) ---
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# --- app layer (only re-copies source, never re-installs deps) ---
COPY . .

EXPOSE 8002
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

CMD ["uvicorn", "mcp.broker.main:app", "--host", "0.0.0.0", "--port", "8002"]
