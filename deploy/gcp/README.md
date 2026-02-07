# Axion GCP Deployment

This directory contains all configuration and scripts needed to deploy Axion on Google Cloud Platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Google Cloud Platform                        │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Compute Engine VM                            │  │
│  │  ┌──────────┐  ┌────────────────┐  ┌─────────────────────────┐ │  │
│  │  │  nginx   │──│ axion-backend  │──│  Cloud SQL Auth Proxy   │ │  │
│  │  │ (proxy)  │  │   (FastAPI)    │  │                         │ │  │
│  │  └────┬─────┘  └────────────────┘  └───────────┬─────────────┘ │  │
│  │       │                                         │               │  │
│  │  ┌────┴─────┐  ┌────────────┐                   │               │  │
│  │  │ Frontend │  │ Storybook  │ (dev/staging)     │               │  │
│  │  │ (Static) │  │  :6006     │                   │               │  │
│  │  └──────────┘  └────────────┘                   │               │  │
│  └─────────────────────────────────────────────────┼───────────────┘  │
│                                                    │                  │
│  ┌─────────────────────────┐  ┌───────────────────┴────────────────┐ │
│  │    Cloud Storage        │  │         Cloud SQL (PostgreSQL)     │ │
│  │  (Artifact Storage)     │  │                                    │ │
│  └─────────────────────────┘  └────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and configured
3. **Terraform** >= 1.0 installed
4. **GitHub repository** with Actions enabled

## Initial Setup

### 1. Create GCP Project and Enable APIs

```bash
# Set project ID
export PROJECT_ID="your-project-id"

# Create project (if needed)
gcloud projects create $PROJECT_ID

# Set default project
gcloud config set project $PROJECT_ID

# Enable billing (via console)
# https://console.cloud.google.com/billing
```

### 2. Create Terraform State Bucket

```bash
gsutil mb -l asia-northeast1 gs://${PROJECT_ID}-terraform-state
gsutil versioning set on gs://${PROJECT_ID}-terraform-state
```

### 3. Deploy Infrastructure with Terraform

```bash
cd deploy/gcp/terraform

# Initialize Terraform
terraform init -backend-config="bucket=${PROJECT_ID}-terraform-state"

# Create terraform.tfvars
cat > terraform.tfvars << EOF
project_id  = "${PROJECT_ID}"
region      = "asia-northeast1"
zone        = "asia-northeast1-a"
environment = "production"
db_password = "YOUR_SECURE_PASSWORD"
EOF

# Plan and apply
terraform plan
terraform apply
```

### 4. Configure GitHub Repository Secrets

After Terraform applies, configure these secrets in your GitHub repository:

| Secret Name                      | Description                | Source                                        |
| -------------------------------- | -------------------------- | --------------------------------------------- |
| `GCP_PROJECT_ID`                 | GCP Project ID             | Your project ID                               |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Workload Identity Provider | Terraform output `workload_identity_provider` |
| `GCP_SERVICE_ACCOUNT`            | Service Account email      | Terraform output `github_service_account`     |
| `CLOUD_SQL_INSTANCE`             | Cloud SQL connection name  | Terraform output `cloud_sql_connection_name`  |
| `DB_USER`                        | Database username          | `axion`                                       |
| `DB_PASSWORD`                    | Database password          | Your secure password                          |
| `DB_NAME`                        | Database name              | `axion`                                       |

### 5. Configure GitHub Repository Variables

| Variable Name  | Description           | Example                        |
| -------------- | --------------------- | ------------------------------ |
| `GCP_REGION`   | GCP Region            | `asia-northeast1`              |
| `GCE_INSTANCE` | VM instance name      | `axion-vm`                     |
| `GCE_ZONE`     | GCE zone              | `asia-northeast1-a`            |
| `GCS_BUCKET`   | Artifacts bucket name | `your-project-axion-artifacts` |
| `APP_DOMAIN`   | Application domain    | `axion.example.com`            |

## Deployment

Deployment is automated via GitHub Actions. The workflow triggers on:

- Push to `main` branch
- Manual workflow dispatch

### Manual Deployment

```bash
gh workflow run deploy-gcp.yml -f environment=production
```

### Workflow Steps

1. **Test** - Run linting, type checking, and unit tests
2. **Build** - Build backend and frontend applications
3. **Deploy** - Upload artifacts to GCS and deploy to VM

## File Structure

```
deploy/gcp/
├── README.md           # This file
├── nginx.conf          # nginx configuration (production)
├── nginx-dev.conf      # nginx configuration (staging/dev with Storybook)
├── vm-setup.sh         # VM initial setup script
├── deploy.sh           # Deployment script
├── env.template        # Environment variables template
└── terraform/
    └── main.tf         # Terraform infrastructure
```

## VM Services

The VM runs the following services:

| Service         | Port | Description                              |
| --------------- | ---- | ---------------------------------------- |
| nginx           | 80   | Reverse proxy for frontend and API       |
| nginx           | 6006 | Storybook (staging/dev environment only) |
| axion-backend   | 8000 | FastAPI backend (internal only)          |
| cloud-sql-proxy | 5432 | Cloud SQL connection proxy               |

## Storybook Deployment (Development Environment)

Storybook is automatically deployed when:
- Deploying to `staging` environment
- Pushing to `develop` branch

### Manual Deployment with Storybook

```bash
gh workflow run deploy-gcp.yml -f environment=staging -f deploy_storybook=true
```

### Access Storybook

After deployment to staging, access Storybook at:
```
http://<VM_EXTERNAL_IP>:6006
```

### Firewall Configuration

For staging VMs, ensure the `axion-web-dev` tag is applied to enable port 6006 access:

```bash
gcloud compute instances add-tags axion-vm \
  --zone=asia-northeast1-a \
  --tags=axion-web-dev
```

## Maintenance

### SSH into VM

```bash
gcloud compute ssh axion-vm --zone=asia-northeast1-a
```

### View Application Logs

```bash
# Backend logs
sudo journalctl -u axion-backend -f

# nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Manual Rollback

```bash
gcloud compute ssh axion-vm --zone=asia-northeast1-a --command="
  sudo rm -rf /opt/axion
  sudo mv /opt/axion-backup /opt/axion
  sudo systemctl restart axion-backend
  sudo systemctl restart nginx
"
```

### Database Migrations

Migrations run automatically during deployment. For manual migrations:

```bash
gcloud compute ssh axion-vm --zone=asia-northeast1-a --command="
  cd /opt/axion
  source .venv/bin/activate
  alembic upgrade head
"
```

## Security Notes

1. **VM Access** - SSH access is restricted to IAP (Identity-Aware Proxy)
2. **Database** - Cloud SQL uses private IP only (no public exposure)
3. **Secrets** - All sensitive values stored in GitHub Secrets
4. **IAM** - Workload Identity Federation (no service account keys)

## Cost Estimation

| Resource      | Specification | ~Monthly Cost (USD) |
| ------------- | ------------- | ------------------- |
| GCE VM        | e2-small      | ~$13                |
| Cloud SQL     | db-f1-micro   | ~$7                 |
| Cloud Storage | <10GB         | ~$0.2               |
| **Total**     |               | **~$20**            |

*Costs vary by region and usage. Use [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator) for accurate estimates.*

## Troubleshooting

### Health Check Fails

```bash
# Check if backend is running
sudo systemctl status axion-backend

# Check nginx configuration
sudo nginx -t

# Check Cloud SQL Proxy
sudo systemctl status cloud-sql-proxy
```

### Database Connection Issues

```bash
# Verify Cloud SQL Proxy is running
sudo systemctl status cloud-sql-proxy

# Test local connection
psql -h localhost -U axion -d axion
```

### Deployment Stuck

```bash
# Check GCS for artifacts
gsutil ls gs://YOUR_BUCKET-deploy/releases/

# Check VM deployment logs
sudo journalctl -u axion-backend --since "10 minutes ago"
```
