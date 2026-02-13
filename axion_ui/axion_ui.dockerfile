FROM node:22-slim

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10.28.0 --activate

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . ./

# Build argument for production builds
ARG BUILD_MODE=development
RUN if [ "$BUILD_MODE" = "production" ]; then pnpm build; fi

# Expose ports (Vite dev: 5173, Storybook: 6006)
EXPOSE 5173 6006

# Default command (can be overridden)
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
