FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/axion ./src/axion
COPY src/axion_server ./src/axion_server

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "axion_server.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
