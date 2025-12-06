# syntax=docker/dockerfile:1
# Stage 1: Builder
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Runner
FROM python:3.10-slim

WORKDIR /app

# Install runtime libs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements just to know what we installed (metadata)
COPY --from=builder /app/requirements.txt .

# MOUNT the wheels from builder stage, install them, and detach.
# The wheels themselves are NEVER copied to the final image layer.
RUN --mount=type=bind,from=builder,source=/app/wheels,target=/wheels \
    pip install --no-cache /wheels/*

COPY . .
RUN chown -R appuser:appuser /app

USER appuser
CMD ["python", "main.py"]