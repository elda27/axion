#!/bin/bash
# VM Initial Setup Script for Axion Lab on GCP
# This script runs once during VM provisioning

set -e

echo "=== Starting Axion Lab VM Setup ==="

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
useradd -m -s /bin/bash axion-lab || true

# Create application directories
mkdir -p /opt/axion_lab
mkdir -p /var/www/axion-lab-ui
mkdir -p /var/www/axion-lab-storybook
mkdir -p /var/log/axion_lab

# Set permissions
chown -R axion-lab:axion-lab /opt/axion_lab
chown -R axion-lab:axion-lab /var/www/axion-lab-ui
chown -R axion-lab:axion-lab /var/www/axion-lab-storybook
chown -R axion-lab:axion-lab /var/log/axion_lab

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
User=axion-lab
ExecStart=/usr/local/bin/cloud-sql-proxy --port 5432 ${CLOUD_SQL_INSTANCE}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Axion Lab Backend
cat > /etc/systemd/system/axion-lab-backend.service << 'EOF'
[Unit]
Description=Axion Lab Backend API
After=network.target cloud-sql-proxy.service
Requires=cloud-sql-proxy.service

[Service]
Type=simple
User=axion-lab
WorkingDirectory=/opt/axion_lab
EnvironmentFile=/opt/axion_lab/.env
ExecStart=/opt/axion_lab/.venv/bin/uvicorn axion_lab_server.apps.api.app:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable services
systemctl daemon-reload
systemctl enable nginx
systemctl enable axion-lab-backend

echo "=== Axion Lab VM Setup Complete ==="
