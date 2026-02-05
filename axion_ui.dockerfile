FROM node:22-slim

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10.28.0 --activate

# Copy package files
COPY src/axion_ui/package.json src/axion_ui/pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY src/axion_ui/ ./

# Expose Storybook port
EXPOSE 6006

# Run Storybook dev server
CMD ["pnpm", "storybook"]
