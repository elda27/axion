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

`axion-lab server` automatically runs migrations before startup. By default it uses SQLite + file storage for local development (and respects explicit environment variables when provided).

```bash
uv run axion-lab server --reload --host 0.0.0.0 --port 8000
```

Default local values:

- `DATABASE_URL=sqlite+aiosqlite:///./axion_lab.db`
- `OBJECT_STORE_PROVIDER=file`
- `OBJECT_STORE_LOCAL_PATH=./data/object_store`

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
