#!/bin/bash
# Axion Deployment Script for GCP VM
# This script is executed via SSH from GitHub Actions

set -e

DEPLOY_DIR="/opt/axion"
UI_DIR="/var/www/axion-ui"
BACKUP_DIR="/opt/axion-backup"

echo "=== Starting Axion Deployment ==="

# Create backup of current deployment
if [ -d "$DEPLOY_DIR" ]; then
    echo "Creating backup..."
    rm -rf "$BACKUP_DIR"
    cp -r "$DEPLOY_DIR" "$BACKUP_DIR" || true
fi

# Extract deployment artifacts
echo "Extracting backend..."
cd /tmp
tar -xzf axion-backend.tar.gz -C "$DEPLOY_DIR"

echo "Extracting frontend..."
rm -rf "$UI_DIR"/*
tar -xzf axion-frontend.tar.gz -C "$UI_DIR"

# Set up Python virtual environment
echo "Setting up Python environment..."
cd "$DEPLOY_DIR"
~/.local/bin/uv venv .venv --python=3.12
~/.local/bin/uv sync --frozen --no-dev

# Run database migrations
echo "Running database migrations..."
source .venv/bin/activate
alembic upgrade head
deactivate

# Copy nginx configuration
echo "Configuring nginx..."
sudo cp "$DEPLOY_DIR/deploy/gcp/nginx.conf" /etc/nginx/sites-available/axion
sudo ln -sf /etc/nginx/sites-available/axion /etc/nginx/sites-enabled/axion
sudo nginx -t

# Restart services
echo "Restarting services..."
sudo systemctl restart axion-backend
sudo systemctl restart nginx

# Health check
echo "Performing health check..."
sleep 5
for i in {1..10}; do
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        echo "Health check passed!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "Health check failed!"
        exit 1
    fi
    echo "Waiting for service to be ready... ($i/10)"
    sleep 3
done

echo "=== Deployment Complete ==="
