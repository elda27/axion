# Axion Lab

Backend package for the Axion Lab experiment evaluation system. Provides the FastAPI server, data models, DP runner, and storage adapters.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
# Install dependencies
uv sync --all-extras
```

## Build

```bash
# Build the Python package
uv build

# Or from the repository root
make build-Axion Lab
```

## Usage

### Start the API server

```bash
uv run uvicorn axion_lab_server.apps.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Run tests

```bash
uv run pytest
```

### Lint

```bash
uv run ruff check src/
```

## Project Structure

```
src/
├── axion_lab/            # Core library (models, repositories, storage, DP)
├── axion_lab_server/     # FastAPI application and routers
└── axion_lab_alembic/    # Database migrations
```
