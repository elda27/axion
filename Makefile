.PHONY: build build-dev build-compose start-dev start-compose start-compose-dev build-axion-lab build-axion-lab-ui watch watch-axion-lab watch-axion-lab-ui

# Build all packages
build: build-axion-lab build-axion-lab-ui

# Build axion-lab Python package
build-axion-lab:
	cd axion_lab && uv build

# Build axion_lab_ui frontend package
build-axion-lab-ui:
	cd axion_lab_ui && pnpm install && pnpm build

# Watch all packages for changes and rebuild
watch:
	$(MAKE) watch-axion-lab & $(MAKE) watch-axion-lab-ui & wait

# Watch axion-lab backend for changes (auto-reload server)
watch-axion-lab:
	cd axion_lab && uv run uvicorn axion_lab_server.apps.api.app:app --reload --host 0.0.0.0 --port 8000

# Watch axion_lab_ui frontend for changes (Vite dev server)
watch-axion-lab-ui:
	cd axion_lab_ui && pnpm dev

# Build local development runtime (Python + UI)
build-dev:
	cd axion_lab && uv sync --all-extras
	cd axion_lab_ui && pnpm install && pnpm build-storybook

# Build Docker images for running axion-lab in containers
build-compose:
	docker build -f axion_lab/axion_lab.dockerfile -t axion-lab:latest axion_lab
	docker build -f axion_lab/axion_lab_server.dockerfile -t axion-lab-server:latest axion_lab
	docker build -f axion_lab/axion_lab_alembic.dockerfile -t axion-lab-alembic:latest axion_lab
	docker build -f axion_lab_ui/axion_lab_ui.dockerfile -t axion-lab-ui:latest axion_lab_ui

# Start local development servers
start-dev:
	cd axion_lab && uv run uvicorn axion_lab_server.apps.api.app:app --reload --host 0.0.0.0 --port 8000

# Start axion-lab with Docker Compose (includes all services)
start-compose:
	docker compose up -d

# Start development environment with hot-reload (Docker)
start-compose-dev:
	docker compose -f compose.dev.yml up -d

# Start Storybook in development mode (Docker)
storybook-dev:
	docker compose -f compose.dev.yml up -d axion-lab-ui

# Start Storybook locally (without Docker)
storybook-local:
	cd axion_lab_ui && pnpm storybook

# Build Storybook static files
storybook-build:
	cd axion_lab_ui && pnpm build-storybook

# Stop Storybook container
storybook-stop:
	docker compose -f compose.dev.yml stop axion-lab-ui
