# Multi-stage build for FastAPI Agent
FROM python:3.12-alpine as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    curl \
    && rm -rf /var/cache/apk/*

# Install uv
RUN pip install --no-cache-dir uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Install Python dependencies using uv
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py ./

# Create non-root user for security
RUN adduser -D -s /bin/sh app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 