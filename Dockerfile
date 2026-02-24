# Multi-stage build for Kenya Legal AI
# 1. Build stage for Python dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 2. Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src ./src
COPY frontend ./frontend
COPY .env.example ./.env.production

# Create data directories
RUN mkdir -p data/raw data/processed data/embeddings

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# Expose FastAPI port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
