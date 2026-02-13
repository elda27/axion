FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock alembic.ini ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/axion ./src/axion
COPY src/axion_server ./src/axion_server
COPY src/axion_alembic ./src/axion_alembic

# Run migrations
CMD ["uv", "run", "alembic", "upgrade", "head"]
