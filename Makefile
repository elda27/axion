.PHONY: build-dev build-compose start-dev start-compose

# Build local development runtime (Python + UI)
build-dev:
	uv sync --all-extras
	cd src/axion_ui && pnpm install && pnpm build-storybook

# Build Docker images for running axion in containers
build-compose:
	docker compose build

# Start local development servers
start-dev:
	uv run uvicorn axion.main:app --reload --host 0.0.0.0 --port 8000

# Start axion with Docker Compose (includes all services)
start-compose:
	docker compose up -d
