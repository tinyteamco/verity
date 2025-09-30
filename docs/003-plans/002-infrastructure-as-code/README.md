# Infrastructure as Code Implementation Plan

**Date:** 2025-09-30
**Status:** Implementation in progress

## Context

We're at a critical juncture where adding IaC now prevents significant technical debt later. Current infrastructure is manually deployed via GitHub Actions CD, but not codified. We're about to add Firebase Hosting integration and LLM services, making this the optimal time to establish IaC patterns.

## Decision: Pulumi in Monorepo

### Why Pulumi?
- **Python-native**: Matches our backend language (Python 3.12)
- **Real programming language**: Type checking, IDE support, reusable functions
- **GCP-first class support**: Official Google provider with excellent documentation
- **State management options**: Cloud-hosted or self-managed (GCS)

### Why Monorepo?
- **Atomic changes**: Code + infrastructure changes in single commits
- **Single source of truth**: No cross-repo coordination overhead
- **Easier reviews**: See full context of feature + infra requirements
- **Security via CODEOWNERS**: Restrict `/infra/*` changes to admins without separate repo

### Alternative Considered: Terraform
- ❌ HCL is less expressive than Python
- ❌ No native type checking
- ❌ Larger ecosystem but less GCP-focused than Pulumi's Google partnership

## Architecture

### Repository Structure

```
verity/
├── infra/                       # NEW: Infrastructure as Code
│   ├── .mise.toml              # Python 3.12 + pulumi CLI
│   ├── Pulumi.yaml             # Project config
│   ├── Pulumi.dev.yaml         # Dev stack config
│   ├── Pulumi.prod.yaml        # Prod stack config
│   ├── __main__.py             # Main infrastructure definition
│   ├── requirements.txt        # pulumi + pulumi-gcp
│   └── README.md               # Infra-specific docs
├── backend/                     # Existing application code
├── frontend/                    # Future: React/Vue app
├── .github/
│   └── workflows/
│       ├── deploy-backend.yml   # Existing: deploys code
│       └── deploy-infra.yml     # NEW: deploys infrastructure
└── CODEOWNERS                   # NEW: Protect infra changes
```

### State Management: Pulumi Cloud

**Decision: Use Pulumi Cloud for state (Option 1)**

Rationale:
- ✅ Free tier sufficient for our needs (unlimited state storage, 3 team members)
- ✅ Web UI for inspecting state and history
- ✅ Built-in secrets encryption
- ✅ Webhook integrations for Slack/Discord notifications
- ✅ Can migrate to self-hosted GCS later if needed (`pulumi stack export`)

Alternative (deferred): Self-hosted GCS backend
- Would require bucket setup and versioning configuration
- No UI for state inspection
- Saves $0/month but adds operational complexity

### Deployment Model: CI-Only

**Decision: Only GitHub Actions can deploy infrastructure**

Rationale:
- ✅ Audit trail: Every change tied to commit + PR
- ✅ Peer review: CODEOWNERS forces approval
- ✅ Consistency: No "works on my machine"
- ✅ Security: No local credentials to leak

**Local development: Preview only**
```bash
pulumi preview    # ✅ Read-only, safe
pulumi up         # ❌ Blocked (CI only)
```

If testing locally is absolutely needed:
1. Use personal GCP account via `gcloud auth application-default login`
2. Run in isolated test project
3. Never commit from local (CI must apply)

## GCP Setup

### Bootstrap (Manual, One-Time)

These steps happen **outside the repository** to bootstrap the infrastructure:

```bash
# 1. Create/configure GCP project
export PROJECT_ID="verity-platform-473406"
export PROJECT_NUMBER="<your-project-number>"
export REGION="us-central1"

gcloud config set project $PROJECT_ID

# 2. Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com

# 3. Create service account for Pulumi deployments
gcloud iam service-accounts create pulumi-deployer \
  --display-name="Pulumi Infrastructure Deployer" \
  --description="Service account for CI/CD infrastructure deployments"

# 4. Grant necessary permissions
# Note: Starting with Editor role, will refine to least-privilege later
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:pulumi-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:pulumi-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:pulumi-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/resourcemanager.projectIamAdmin"

# 5. Set up Workload Identity Federation for GitHub Actions
# This allows GitHub to authenticate as the service account WITHOUT JSON keys

# Create workload identity pool
gcloud iam workload-identity-pools create github \
  --location=global \
  --display-name="GitHub Actions Pool" \
  --description="Identity pool for GitHub Actions workflows"

# Create OIDC provider for GitHub
gcloud iam workload-identity-pools providers create-oidc github \
  --location=global \
  --workload-identity-pool=github \
  --display-name="GitHub OIDC Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository_owner=='<your-github-username>'"

# Bind service account to GitHub repository
gcloud iam service-accounts add-iam-policy-binding \
  pulumi-deployer@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/<your-github-username>/verity"

# Output values needed for GitHub Actions
echo "✅ Bootstrap complete!"
echo ""
echo "Add these to your GitHub Actions workflow:"
echo "  workload_identity_provider: projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github"
echo "  service_account: pulumi-deployer@$PROJECT_ID.iam.gserviceaccount.com"
```

### GitHub Secrets Setup

**Required secrets in GitHub repo settings:**

1. **PULUMI_ACCESS_TOKEN**
   - Sign up at https://app.pulumi.com
   - Go to Settings → Access Tokens
   - Create new token
   - Add to GitHub: Settings → Secrets and variables → Actions → New repository secret

2. **Workload Identity** (configured via bootstrap script above)
   - No secrets needed! GitHub's OIDC token is used automatically
   - More secure than JSON keys

## Resources to Codify

### Phase 1: Foundation (This iteration)

1. **Cloud SQL Instance** ✅ Critical
   - PostgreSQL 16
   - Private IP + Cloud SQL Proxy
   - Automated backups
   - Currently: Manually created

2. **Service Accounts** ✅ Critical
   - Backend runtime service account
   - Cloud SQL client permissions
   - Secret Manager access
   - Currently: Using default compute SA (too broad)

3. **Secrets in Secret Manager** ✅ Critical
   - DATABASE_URL
   - Future: API keys for LLM providers
   - Currently: Environment variables in Cloud Run

4. **Cloud Run Service** ✅ Important
   - Backend API deployment configuration
   - VPC connector for Cloud SQL
   - Environment variables
   - Currently: Deployed via GitHub Actions but config not in code

### Phase 2: Firebase Integration (Next iteration)

5. **Firebase Hosting** 🔄 Planned
   - Rewrites to proxy `/api/**` to Cloud Run
   - Custom domain configuration
   - SSL certificate management

6. **Firebase Project Configuration** 🔄 Planned
   - Auth configuration
   - Security rules
   - Extensions (if any)

### Phase 3: Advanced Features (Future)

7. **Cloud Storage Buckets** ⏳ Future
   - Audio recordings (if not using MinIO)
   - Backup storage
   - Static assets

8. **Cloud Pub/Sub Topics** ⏳ Future
   - Async job processing for LLM analysis
   - Event-driven architecture

9. **Cloud Tasks Queues** ⏳ Future
   - Scheduled jobs
   - Retry logic for LLM calls

10. **Cloud Armor** ⏳ Future
    - WAF rules
    - Rate limiting
    - DDoS protection

## Security Model

### CODEOWNERS

**File:** `/.github/CODEOWNERS`

```
# Infrastructure changes require admin approval
/infra/ @jkp-admin-team
/scripts/bootstrap-*.sh @jkp-admin-team
/.github/workflows/deploy-infra.yml @jkp-admin-team
```

### Branch Protection

**Settings → Branches → Add rule for `main`:**
- ✅ Require pull request reviews (1 approval)
- ✅ Require CODEOWNERS review
- ✅ Require status checks: `test` workflow must pass
- ✅ Require conversation resolution
- ✅ Do not allow bypassing (even for admins)

### IAM Hierarchy

```
GCP Project: verity-platform-473406
├── pulumi-deployer@... (Service Account)
│   ├── roles/editor (resource management)
│   ├── roles/iam.serviceAccountAdmin (create SAs)
│   └── roles/resourcemanager.projectIamAdmin (grant permissions)
│
├── backend-runtime@... (Service Account) [TO BE CREATED]
│   ├── roles/cloudsql.client (connect to DB)
│   ├── roles/secretmanager.secretAccessor (read secrets)
│   └── roles/storage.objectViewer (read audio files)
│
└── GitHub Actions (via Workload Identity)
    └── Impersonates: pulumi-deployer@...
```

## Implementation Checklist

### Manual Setup (Do Once)
- [ ] Run bootstrap script to create `pulumi-deployer` service account
- [ ] Set up Workload Identity Federation for GitHub
- [ ] Create Pulumi Cloud account
- [ ] Generate Pulumi access token
- [ ] Add `PULUMI_ACCESS_TOKEN` to GitHub secrets
- [ ] Add CODEOWNERS file
- [ ] Configure branch protection rules

### Code Changes (This PR)
- [ ] Create `/infra` directory structure
- [ ] Write `Pulumi.yaml` project configuration
- [ ] Implement `__main__.py` with Phase 1 resources
- [ ] Create `.github/workflows/deploy-infra.yml`
- [ ] Update CLAUDE.md with IaC documentation
- [ ] Update root README.md with infra commands

### Validation
- [ ] Run `pulumi preview` locally (read-only)
- [ ] Trigger workflow manually to deploy to dev stack
- [ ] Verify resources created in GCP Console
- [ ] Test backend still works after IaC migration
- [ ] Document any manual migration steps needed

## Migration Strategy

### Importing Existing Resources

Current infrastructure exists but isn't managed by Pulumi. We have two options:

**Option A: Import existing resources**
```bash
pulumi import gcp:sql/databaseInstance:DatabaseInstance postgres <instance-name>
pulumi import gcp:cloudrun/service:Service backend <service-name>
```
- ✅ Zero downtime
- ❌ Complex, error-prone
- ❌ Requires exact resource IDs

**Option B: Fresh deployment to new stack (Recommended)**
1. Create new `dev-v2` stack with Pulumi
2. Deploy all resources from scratch
3. Migrate data from old DB to new
4. Switch DNS/traffic to new stack
5. Delete old manually-created resources

We'll use **Option B** for cleaner state.

## Rollback Plan

If Pulumi deployment fails:

1. **Infrastructure still broken:**
   - Revert PR
   - Trigger workflow again to apply previous state
   - Pulumi handles drift detection automatically

2. **Need emergency manual fix:**
   - Make change in GCP Console
   - Document change in incident log
   - Update Pulumi code to match in next PR
   - Run `pulumi refresh` to sync state

## Success Metrics

- ✅ All Phase 1 resources managed by Pulumi (Cloud SQL, SAs, Secrets, Cloud Run)
- ✅ Infrastructure changes only via GitHub PRs
- ✅ Zero manual resource creation in GCP Console
- ✅ Deployment workflow runs in < 5 minutes
- ✅ Backend continues to work (health check passes)
- ✅ Can recreate entire environment from code (`pulumi up` on empty project)

## Timeline

- **Week 1:** Bootstrap + Phase 1 implementation (this iteration)
- **Week 2:** Firebase Hosting integration (Phase 2)
- **Week 3+:** Advanced features as needed (Phase 3)

## References

- [Pulumi GCP Provider](https://www.pulumi.com/registry/packages/gcp/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Pulumi Best Practices](https://www.pulumi.com/docs/using-pulumi/best-practices/)

## Open Questions

1. **Database migration:** Should we import existing Cloud SQL instance or create new?
   - **Decision:** Create new in dev stack, test thoroughly, then apply to prod

2. **Secrets rotation:** How often should we rotate service account credentials?
   - **Decision:** Quarterly rotation, automated via Pulumi + Secret Manager versioning

3. **Cost monitoring:** Should we set up billing alerts in Pulumi?
   - **Decision:** Yes, add in Phase 1 as Budget resource

4. **Disaster recovery:** What's RTO/RPO for database?
   - **Decision:** RTO = 1 hour, RPO = 15 minutes (automated backups + PITR)