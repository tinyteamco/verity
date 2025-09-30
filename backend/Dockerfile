# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/

# Copy Alembic configuration for database migrations
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
# Use /bin/sh to allow PORT env var substitution
CMD ["sh", "-c", "python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]