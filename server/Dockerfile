# SUBFRACTURE FastMCP Server Dockerfile
# Multi-stage build for production optimization

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r subfracture && useradd -r -g subfracture subfracture

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Development stage
FROM base as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R subfracture:subfracture /app
USER subfracture

EXPOSE 8001 8000

CMD ["python", "main.py"]

# Production stage
FROM base as production

WORKDIR /app

# Copy requirements and install production dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Create logs directory
RUN mkdir -p logs && chown -R subfracture:subfracture /app
USER subfracture

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

EXPOSE 8001 8000

CMD ["python", "main.py"]