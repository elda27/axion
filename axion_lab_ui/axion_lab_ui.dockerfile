FROM node:22-slim

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10.28.0 --activate

# Copy workspace root package files and lockfile
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY axion_lab_ui/package.json ./axion_lab_ui/

# Install dependencies
RUN pnpm install --frozen-lockfile --filter axion_lab_ui

# Copy source code
COPY axion_lab_ui/ ./axion_lab_ui/

# Build argument for production builds
ARG BUILD_MODE=development
RUN if [ "$BUILD_MODE" = "production" ]; then \
  pnpm install --frozen-lockfile --filter axion_lab_ui && \
  pnpm --filter axion_lab_ui build; \
  fi

WORKDIR /app/axion_lab_ui

# Expose ports (Vite dev: 5173, Storybook: 6006)
EXPOSE 5173 6006

# Default command (can be overridden)
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
