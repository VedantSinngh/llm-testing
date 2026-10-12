# Multi-stage production Dockerfile for PromptLab
FROM python:3.11-slim as base

# Set environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime dependencies and curl for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and application workspace
RUN useradd --create-home --shell /bin/bash promptlab
WORKDIR /app

# Copy dependency definition and install packages
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && \
    pip install ".[dev]"

# Copy source code, seed datasets, and management scripts
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Install the promptlab package in editable mode
RUN pip install -e .

# Create directory for persistent SQLite storage and adjust permissions
RUN mkdir -p /app/data && chown -R promptlab:promptlab /app

USER promptlab

# Expose FastAPI (8000) and Streamlit (8501) ports
EXPOSE 8000
EXPOSE 8501

# Default command: launch the FastAPI backend (respecting $PORT if set by Render / cloud hosts)
CMD ["sh", "-c", "uvicorn promptlab.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
