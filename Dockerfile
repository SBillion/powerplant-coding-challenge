# Use Python 3.14 slim image
FROM python:3.14-slim AS base

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Production stage
FROM base AS production

# Install dependencies (production only, no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/
COPY main.py ./

# Expose port 8888
EXPOSE 8888

# Run the application
CMD ["uv", "run", "python", "main.py"]

# Development stage
FROM base AS development

# Install all dependencies including dev dependencies
RUN uv sync --frozen

# Copy application code
COPY app/ ./app/
COPY main.py ./
COPY tests/ ./tests/
COPY example_payloads/ ./example_payloads/

# Expose port 8888
EXPOSE 8888

# Run with hot-reload enabled
CMD ["uv", "run", "python", "main.py"]
