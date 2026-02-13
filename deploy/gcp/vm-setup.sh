#!/bin/bash
# VM Initial Setup Script for Axion on GCP
# This script runs once during VM provisioning

set -e

echo "=== Starting Axion VM Setup ==="

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    nginx \
    python3.12 \
    python3.12-venv \
    python3-pip \
    nodejs \
    npm \
    git \
    curl \
    wget \
    unzip \
    supervisor

# Install pnpm
npm install -g pnpm@10

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Create application user
useradd -m -s /bin/bash axion || true

# Create application directories
mkdir -p /opt/axion
mkdir -p /var/www/axion-ui
mkdir -p /var/www/axion-storybook
mkdir -p /var/log/axion

# Set permissions
chown -R axion:axion /opt/axion
chown -R axion:axion /var/www/axion-ui
chown -R axion:axion /var/www/axion-storybook
chown -R axion:axion /var/log/axion

# Configure nginx
rm -f /etc/nginx/sites-enabled/default

# Install Cloud SQL Auth Proxy
wget https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.2/cloud-sql-proxy.linux.amd64 -O /usr/local/bin/cloud-sql-proxy
chmod +x /usr/local/bin/cloud-sql-proxy

# Create systemd service for Cloud SQL Proxy
cat > /etc/systemd/system/cloud-sql-proxy.service << 'EOF'
[Unit]
Description=Cloud SQL Auth Proxy
After=network.target

[Service]
Type=simple
User=axion
ExecStart=/usr/local/bin/cloud-sql-proxy --port 5432 ${CLOUD_SQL_INSTANCE}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Axion Backend
cat > /etc/systemd/system/axion-backend.service << 'EOF'
[Unit]
Description=Axion Backend API
After=network.target cloud-sql-proxy.service
Requires=cloud-sql-proxy.service

[Service]
Type=simple
User=axion
WorkingDirectory=/opt/axion
EnvironmentFile=/opt/axion/.env
ExecStart=/opt/axion/.venv/bin/uvicorn axion_server.apps.api.app:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable services
systemctl daemon-reload
systemctl enable nginx
systemctl enable axion-backend

echo "=== Axion VM Setup Complete ==="
