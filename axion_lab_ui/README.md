# axion_lab_ui

Frontend UI package for the Axion Lab experiment evaluation system. Built with React, Vite, and MUI. Uses Storybook for component development.

## Prerequisites

- Node.js
- [pnpm](https://pnpm.io/)

## Setup

```bash
# Install dependencies
pnpm install
```

## Build

```bash
# Build the application
pnpm build

# Or from the repository root
make build-axion-lab-ui
```

### Build Storybook

```bash
# Build Storybook static files
pnpm build-storybook

# Or from the repository root
make storybook-build
```

## Development

```bash
# Start Vite dev server
pnpm dev

# Start Storybook dev server (port 6006)
pnpm storybook
```

## Testing

```bash
pnpm test
```

## Project Structure

```
src/        # Application source code
stories/    # Storybook stories
.storybook/ # Storybook configuration
```
