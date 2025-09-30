# Verity Infrastructure

Infrastructure as Code for the Verity UXR platform using Pulumi and Google Cloud Platform.

## Prerequisites

- Pulumi Cloud account: https://app.pulumi.com
- GCP project bootstrapped (run `/scripts/bootstrap-gcp-pulumi.sh` once)
- mise installed: `curl https://mise.run | sh`

## Setup

```bash
# Install dependencies
cd infra
mise install
mise exec -- uv sync

# Login to Pulumi Cloud
mise exec -- pulumi login
```

## Local Development (Preview Only)

**Important:** Only GitHub Actions can deploy infrastructure. Local commands are read-only.

```bash
# Select stack
mise exec -- pulumi stack select dev

# Preview changes (safe, read-only)
mise exec -- pulumi preview

# View current infrastructure
mise exec -- pulumi stack output

# View stack configuration
mise exec -- pulumi config

# Refresh state from actual GCP resources
mise exec -- pulumi refresh
```

## Stack Configuration

### Dev Stack
- **Purpose:** Development and testing
- **Database:** db-f1-micro (shared core)
- **Cloud Run:** Scale to zero when idle
- **Deletion protection:** Disabled

### Prod Stack
- **Purpose:** Production workloads
- **Database:** db-n1-standard-1 (dedicated CPU)
- **Cloud Run:** Minimum 1 instance always running
- **Deletion protection:** Enabled

## Resources Managed

### Compute
- **Cloud Run Service:** Backend API (`verity-backend-{stack}`)
- **VPC Connector:** Private connectivity to Cloud SQL

### Database
- **Cloud SQL Instance:** PostgreSQL 16 (`verity-db-{stack}`)
- **Database:** `verity`
- **User:** `verity_app`
- **Backups:** Daily at 3 AM UTC, 7-day PITR

### Networking
- **VPC Network:** Custom network for private services
- **Private IP Range:** Allocated for Google services peering
- **VPC Peering:** Connection to Google services

### Security
- **Service Accounts:**
  - `verity-backend-{stack}@...`: Runtime SA for Cloud Run
- **IAM Bindings:**
  - Cloud SQL Client (connect to database)
  - Secret Manager Accessor (read secrets)
- **Secrets:**
  - `verity-database-url-{stack}`: Database connection string

## Deployment

**Only via GitHub Actions:**

1. Go to: https://github.com/<your-org>/verity/actions/workflows/deploy-infra.yml
2. Click "Run workflow"
3. Select stack: `dev` or `prod`
4. Confirm deployment

The workflow will:
- Authenticate via Workload Identity (no keys!)
- Run `pulumi preview` first
- Wait for approval (manual step)
- Run `pulumi up` to apply changes
- Output stack exports

## Outputs

After deployment, view outputs:

```bash
mise exec -- pulumi stack output
```

Key outputs:
- `backend_url`: Cloud Run service URL
- `db_connection_name`: Cloud SQL connection name for proxy
- `backend_service_account`: Service account email for Cloud Run
- `database_url_secret_name`: Secret Manager secret name

## Secrets Management

### Setting Secrets

Secrets are set via Pulumi config (encrypted):

```bash
# Set database password (only in CI, not locally)
mise exec -- pulumi config set db_password --secret

# View secret (shows [secret])
mise exec -- pulumi config get db_password
```

### Accessing Secrets in Code

Cloud Run services access secrets via environment variables configured in `__main__.py`:

```python
envs=[
    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
        name="DATABASE_URL",
        value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
            secret_key_ref=...
        ),
    ),
]
```

## Disaster Recovery

### Database Backup

**Automatic:**
- Daily backups at 3 AM UTC
- 7-day point-in-time recovery (PITR)
- Transaction logs retained for 7 days

**Manual Backup:**
```bash
gcloud sql backups create \
  --instance=verity-db-prod \
  --project=verity-platform-473406
```

**Restore:**
```bash
# Restore to specific timestamp
gcloud sql backups restore <backup-id> \
  --backup-instance=verity-db-prod \
  --backup-project=verity-platform-473406 \
  --target-instance=verity-db-prod-restored
```

### Infrastructure Recovery

**Complete stack recreation:**
```bash
# Via GitHub Actions
# 1. Trigger deploy-infra.yml workflow
# 2. Select stack: prod
# 3. Pulumi will recreate all resources from code

# Resources are immutable - no data loss
# Database data persists (unless deletion_protection=false)
```

## Cost Optimization

### Development
- Cloud Run scales to zero (no idle cost)
- db-f1-micro instance (~$10/month)
- No VPC connector minimum instances

### Production
- Cloud Run minimum 1 instance (~$30/month)
- db-n1-standard-1 instance (~$50/month)
- VPC connector 2 minimum instances (~$20/month)

**Total estimated:** Dev ~$15/month, Prod ~$100/month

## Troubleshooting

### "Resource already exists" error

If importing existing resources:
```bash
mise exec -- pulumi import gcp:sql/databaseInstance:DatabaseInstance postgres <name>
```

### Permission denied errors

Ensure service account has correct roles:
```bash
gcloud projects get-iam-policy verity-platform-473406 \
  --flatten="bindings[].members" \
  --filter="bindings.members:pulumi-deployer@*"
```

### State drift

If manual changes were made in GCP Console:
```bash
# Refresh Pulumi state to match reality
mise exec -- pulumi refresh

# Then update code to match desired state
# Submit PR to codify changes
```

## Security Best Practices

1. **Never commit secrets** - Use Pulumi config with `--secret` flag
2. **No local JSON keys** - Workload Identity only
3. **Least privilege IAM** - Service accounts have minimal permissions
4. **Private networking** - Cloud SQL has no public IP
5. **Deletion protection** - Enabled for prod database
6. **Audit logging** - All changes via GitHub PRs

## References

- [Pulumi GCP Provider](https://www.pulumi.com/registry/packages/gcp/)
- [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/best-practices)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)