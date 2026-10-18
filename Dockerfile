# BUILD STAGE
FROM python:3.12-slim AS builder

# Copy UV binary from official image
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

# Set Working Directory
WORKDIR /app

# UV Docker Optimizations
ENV UV_COMPILE_BYTECODE=1
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_LINK_MODE=copy

# Copy and install dependencies first
COPY pyproject.toml uv.lock .
RUN uv sync --locked --no-install-project --no-dev

# Copy and install the project
COPY /app .
RUN uv sync --locked --no-dev


# PRODUCTION STAGE
FROM python:3.12-slim

# Choose Working Directory
WORKDIR /app

# Run as non-root user for security purposes
RUN useradd -m appuser

# Copy app and dependencies from the Builder Stage
COPY --from=builder --chown=appuser:appuser /app /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Start the FastAPI application
CMD ["/bin/sh", "-c", "exec fastapi run --host 0.0.0.0 --port \"$PORT\" --proxy-headers --forwarded-allow-ips '*'"]
