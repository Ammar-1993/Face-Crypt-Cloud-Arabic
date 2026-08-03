# syntax=docker/dockerfile:1
# ============================================================
# Face-Crypt-Cloud — Dockerfile
# Multi-stage build: compile heavy deps (dlib) in a builder
# stage, keep the final runtime image slim.
# Verified: build-essential + cmake are sufficient to compile
# dlib from source on Debian/Ubuntu; the rest of requirements.txt
# resolves to prebuilt manylinux wheels (verified via a dry-run
# resolve against the exact pinned versions in this repo).
# ============================================================

# ---------- Stage 1: builder ----------
FROM python:3.10-slim AS builder

# cmake + a C++ toolchain are required to compile dlib from source
# (PyPI has no prebuilt Linux wheel for it). libopenblas-dev/liblapack-dev
# are optional but give dlib/numpy a real speed boost for face-encoding math.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libopenblas-dev \
        liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .

# Build wheels once here so the final stage never needs the compiler
# toolchain at all (smaller final image, faster container startup).
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.10-slim

# libgomp1: OpenMP runtime used by numpy/dlib's compiled extensions.
# libopenblas0 + liblapack3: RUNTIME counterparts of the libopenblas-dev /
# liblapack-dev packages installed in the builder stage above. dlib links
# against libopenblas.so.0 at build time, but a multi-stage build only
# carries over the /wheels directory from the builder — not its apt
# packages. Without these two runtime packages here, `import dlib` fails
# at container startup with:
#   ImportError: libopenblas.so.0: cannot open shared object file
# (confirmed via a real deployment log — this is not a hypothetical risk).
#
# NOTE: this image assumes requirements.txt uses opencv-python-headless
# (not opencv-python). The regular opencv-python package additionally
# needs libgl1/libglib2.0-0/libsm6 etc. for GUI features this server-side
# app never uses — headless avoids that whole dependency chain. If you
# keep opencv-python instead, add those packages to the apt-get line below.
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

# Application source
COPY . .

# Secrets are NEVER baked into the image — .env and the Firebase service
# account JSON are provided at runtime via docker-compose (env_file +
# volume mount). See docker-compose.yml and .dockerignore.

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# Production-safe default: waitress via wsgi.py (matches the
# Production Deployment section already documented in README.md).
# docker-compose.yml overrides this command for local development
# to use Flask's auto-reloading dev server instead.
CMD ["python", "wsgi.py"]