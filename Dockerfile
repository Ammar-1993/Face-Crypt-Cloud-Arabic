# syntax=docker/dockerfile:1
# ============================================================
# Face-Crypt-Cloud — Dockerfile
# Optimized Multi-stage build for heavy ML dependencies
# ============================================================

# ---------- Stage 1: Builder ----------
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libopenblas-dev \
        liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libopenblas0 \
        liblapack3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# نسخ الكود الفعلي (هذه الخطوة سريعة جداً)
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["python", "wsgi.py"]