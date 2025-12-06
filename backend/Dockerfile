# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies for building python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies into the venv
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Stage 2: Runner (Final Image)
FROM python:3.10-slim

WORKDIR /app

# Install ONLY runtime system dependencies (libpq for postgres)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy the virtual environment from builder
# This is the key step: We copy the pre-installed environment
COPY --from=builder /opt/venv /opt/venv

# Enable venv in the path
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Permissions
RUN chown -R appuser:appuser /app

# Switch user
USER appuser

# Run
CMD ["python", "main.py"]