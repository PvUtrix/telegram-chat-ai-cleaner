# Multi-stage Docker build for Telegram Chat Analyzer

# Build stage
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy package files and source code
COPY setup.py pyproject.toml ./
COPY src/ ./src/

# Install package in editable mode
RUN pip install -e .

# Production stage
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    # Required for some Python packages
    libgomp1 \
    # For Ollama (if used locally)
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user
RUN useradd --create-home --shell /bin/bash tguser && \
    mkdir -p /app/data && \
    chown -R tguser:tguser /app

# Set working directory
WORKDIR /app

# Copy package files and source code
COPY --chown=tguser:tguser setup.py pyproject.toml ./
COPY --chown=tguser:tguser src/ ./src/

# Install the package in editable mode
RUN pip install -e .

# Copy configuration template
COPY --chown=tguser:tguser env.example .env.example

# Create data directories
RUN mkdir -p data/input data/output data/analysis data/vectors

# Switch to non-root user
USER tguser

# Expose port for web interface
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["tg-analyzer", "web", "--host", "0.0.0.0", "--port", "8000"]

