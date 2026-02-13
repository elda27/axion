.PHONY: build build-dev build-compose start-dev start-compose start-compose-dev build-axion build-axion-ui watch watch-axion watch-axion-ui

# Build all packages
build: build-axion build-axion-ui

# Build axion Python package
build-axion:
	cd axion && uv build

# Build axion_ui frontend package
build-axion-ui:
	cd axion_ui && pnpm install && pnpm build

# Watch all packages for changes and rebuild
watch:
	$(MAKE) watch-axion & $(MAKE) watch-axion-ui & wait

# Watch axion backend for changes (auto-reload server)
watch-axion:
	cd axion && uv run uvicorn axion_server.apps.api.app:app --reload --host 0.0.0.0 --port 8000

# Watch axion_ui frontend for changes (Vite dev server)
watch-axion-ui:
	cd axion_ui && pnpm dev

# Build local development runtime (Python + UI)
build-dev:
	cd axion && uv sync --all-extras
	cd axion_ui && pnpm install && pnpm build-storybook

# Build Docker images for running axion in containers
build-compose:
	docker build -f axion/axion.dockerfile -t axion:latest axion
	docker build -f axion/axion_server.dockerfile -t axion-server:latest axion
	docker build -f axion/axion_alembic.dockerfile -t axion-alembic:latest axion
	docker build -f axion_ui/axion_ui.dockerfile -t axion-ui:latest axion_ui

# Start local development servers
start-dev:
	cd axion && uv run uvicorn axion_server.apps.api.app:app --reload --host 0.0.0.0 --port 8000

# Start axion with Docker Compose (includes all services)
start-compose:
	docker compose up -d

# Start development environment with hot-reload (Docker)
start-compose-dev:
	docker compose -f compose.dev.yml up -d

# Start Storybook in development mode (Docker)
storybook-dev:
	docker compose -f compose.dev.yml up -d axion-ui

# Start Storybook locally (without Docker)
storybook-local:
	cd axion_ui && pnpm storybook

# Build Storybook static files
storybook-build:
	cd axion_ui && pnpm build-storybook

# Stop Storybook container
storybook-stop:
	docker compose -f compose.dev.yml stop axion-ui
