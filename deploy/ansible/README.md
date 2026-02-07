# Axion Ansible Deployment

This directory contains Ansible playbooks and roles for setting up and deploying Axion on GCP VMs.

## Directory Structure

```
deploy/ansible/
├── ansible.cfg              # Ansible configuration
├── inventory/
│   └── hosts.yml            # Inventory file
├── group_vars/
│   ├── all.yml              # Common variables
│   ├── production.yml       # Production environment
│   └── staging.yml          # Staging environment
├── playbooks/
│   ├── setup.yml            # Initial VM setup
│   ├── deploy.yml           # Application deployment
│   └── rollback.yml         # Rollback deployment
└── roles/
    ├── common/              # Base system setup
    ├── python/              # Python and uv installation
    ├── nginx/               # nginx web server
    ├── cloud_sql_proxy/     # Cloud SQL Auth Proxy
    └── axion/               # Axion application
```

## Prerequisites

1. **Ansible installed** (2.10+)
   ```bash
   pip install ansible
   ```

2. **SSH access** to target VMs
3. **Environment variables** set (see below)

## Environment Variables

Set these environment variables before running playbooks:

```bash
# Required
export CLOUD_SQL_INSTANCE="project:region:instance"
export DB_PASSWORD="your-secure-password"
export GCP_PROJECT_ID="your-gcp-project-id"

# Optional
export DB_USER="axion"           # Default: axion
export DB_NAME="axion"           # Default: axion
export GCS_BUCKET="axion-artifacts"

# SSH
export ANSIBLE_SSH_USER="ubuntu"
export ANSIBLE_SSH_KEY="~/.ssh/id_rsa"
export AXION_PROD_HOST="10.0.0.2"
export AXION_STAGING_HOST="10.0.0.3"
```

## Usage

### Initial VM Setup

Run once to set up a new VM:

```bash
cd deploy/ansible

# Setup production VM
ansible-playbook playbooks/setup.yml -l production

# Setup staging VM
ansible-playbook playbooks/setup.yml -l staging

# Setup with specific tags
ansible-playbook playbooks/setup.yml -l production --tags "common,nginx"
```

### Deploy Application

Deploy application code:

```bash
# Set artifact paths
export BACKEND_ARCHIVE="/path/to/axion-backend.tar.gz"
export FRONTEND_ARCHIVE="/path/to/axion-frontend.tar.gz"

# Deploy to production
ansible-playbook playbooks/deploy.yml -l production

# Deploy without migrations
ansible-playbook playbooks/deploy.yml -l production -e "run_migrations=false"

# Deploy specific component
ansible-playbook playbooks/deploy.yml -l production --tags "backend"
ansible-playbook playbooks/deploy.yml -l production --tags "frontend"
```

### Rollback

Rollback to previous deployment:

```bash
ansible-playbook playbooks/rollback.yml -l production
```

## Playbook Tags

### setup.yml

| Tag                    | Description                          |
| ---------------------- | ------------------------------------ |
| `common`, `base`       | Base system packages and user setup  |
| `python`               | Python and uv installation           |
| `nginx`, `web`         | nginx installation and configuration |
| `database`, `cloudsql` | Cloud SQL Proxy setup                |
| `axion`, `app`         | Axion application configuration      |

### deploy.yml

| Tag                      | Description                 |
| ------------------------ | --------------------------- |
| `backup`                 | Backup current deployment   |
| `backend`, `deploy`      | Deploy backend application  |
| `frontend`, `deploy`     | Deploy frontend application |
| `migrations`, `database` | Run database migrations     |
| `restart`, `services`    | Restart services            |
| `health`, `verify`       | Health check                |

## Custom Variables

Override variables using `-e` flag:

```bash
# Custom nginx server name
ansible-playbook playbooks/setup.yml -l production \
  -e "nginx_server_name=axion.example.com"

# Enable SSL
ansible-playbook playbooks/setup.yml -l production \
  -e "ssl_enabled=true" \
  -e "ssl_domain=axion.example.com"

# Custom ports
ansible-playbook playbooks/setup.yml -l production \
  -e "backend_port=9000" \
  -e "cloud_sql_proxy_port=5433"
```

## GitHub Actions Integration

Example integration with GitHub Actions:

```yaml
- name: Setup Ansible
  run: pip install ansible

- name: Run Ansible deployment
  env:
    ANSIBLE_SSH_USER: ubuntu
    ANSIBLE_SSH_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
    AXION_PROD_HOST: ${{ secrets.PROD_VM_IP }}
    CLOUD_SQL_INSTANCE: ${{ secrets.CLOUD_SQL_INSTANCE }}
    DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
    GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
    BACKEND_ARCHIVE: dist/axion-backend.tar.gz
    FRONTEND_ARCHIVE: dist/axion-frontend.tar.gz
  run: |
    cd deploy/ansible
    ansible-playbook playbooks/deploy.yml -l production
```

## Troubleshooting

### SSH Connection Issues

```bash
# Test connectivity
ansible all -m ping

# Run with verbose output
ansible-playbook playbooks/setup.yml -l production -vvv
```

### Service Status

```bash
# Check services on remote host
ansible production -a "systemctl status axion-backend"
ansible production -a "systemctl status cloud-sql-proxy"
ansible production -a "systemctl status nginx"
```

### View Logs

```bash
# View backend logs
ansible production -a "tail -100 /var/log/axion/axion-backend.log"

# View nginx logs
ansible production -a "tail -100 /var/log/axion/nginx_access.log"
```

### Check Ansible Facts

```bash
# Gather and display facts
ansible production -m setup
```

## Security Notes

1. **SSH Keys**: Use SSH key-based authentication only
2. **Secrets**: Never commit secrets to repository
3. **Environment Variables**: Use GitHub Secrets or Vault for CI/CD
4. **Firewall**: Ensure only necessary ports are open (22 for SSH via IAP, 80/443 for HTTP/HTTPS)
