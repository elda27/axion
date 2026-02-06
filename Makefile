.PHONY: build-dev build-compose start-dev start-compose start-compose-dev

# Build local development runtime (Python + UI)
build-dev:
	uv sync --all-extras
	cd src/axion_ui && pnpm install && pnpm build-storybook

# Build Docker images for running axion in containers
build-compose:
	docker build -f axion.dockerfile -t axion:latest .
	docker build -f axion_server.dockerfile -t axion-server:latest .
	docker build -f axion_alembic.dockerfile -t axion-alembic:latest .
	docker build -f axion_ui.dockerfile -t axion-ui:latest .

# Start local development servers
start-dev:
	uv run uvicorn axion.main:app --reload --host 0.0.0.0 --port 8000

# Start axion with Docker Compose (includes all services)
start-compose:
	docker compose up -d

# Start development environment with hot-reload (Docker)
start-compose-dev:
	docker compose -f compose.dev.yml up -d
