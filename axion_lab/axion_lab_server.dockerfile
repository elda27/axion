FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock alembic.ini README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/axion_lab ./src/axion_lab
COPY src/axion_lab_server ./src/axion_lab_server
COPY src/axion_lab_alembic ./src/axion_lab_alembic

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "axion_lab_server.apps.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
