# Infrastructure Quick Start

## First-Time Setup (Do Once)

### 1. Bootstrap GCP
```bash
# From repository root
export GITHUB_REPO="your-username/verity"  # Replace with your GitHub repo
./scripts/bootstrap-gcp-pulumi.sh
```

This creates:
- `pulumi-deployer` service account
- Workload Identity Federation for GitHub
- Required IAM permissions

### 2. Create Pulumi Cloud Account
1. Sign up at https://app.pulumi.com (free)
2. Go to Settings → Access Tokens
3. Create new token
4. Save it (you'll need it next)

### 3. Add GitHub Secrets
Go to your repo: `https://github.com/your-username/verity/settings/secrets/actions`

Add these secrets:
- **PULUMI_ACCESS_TOKEN**: Token from step 2
- **GCP_PROJECT_NUMBER**: Found in GCP Console or from bootstrap script output

### 4. Deploy Infrastructure
1. Go to: https://github.com/your-username/verity/actions/workflows/deploy-infra.yml
2. Click "Run workflow"
3. Select:
   - Stack: `dev`
   - Action: `preview` (first time, to see what will be created)
4. Review the preview output
5. Run again with action: `up` to actually create resources

## Daily Usage

### View Infrastructure
```bash
cd infra
mise exec -- pulumi login
mise exec -- pulumi stack select dev
mise exec -- pulumi stack output  # See all outputs
```

### Make Changes
1. Edit `infra/__main__.py`
2. Commit to branch
3. Create PR
4. Preview shows in CI
5. Merge → triggers deployment

### Emergency Access
If you need to deploy locally (not recommended):
```bash
cd infra
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
mise exec -- pulumi preview  # Always preview first
mise exec -- pulumi up        # Only if absolutely necessary
```

## Troubleshooting

**"Workload Identity error"**
- Check that `GCP_PROJECT_NUMBER` secret is set correctly
- Verify bootstrap script completed successfully

**"Permission denied"**
- Ensure `pulumi-deployer` SA has required roles
- Re-run bootstrap script

**"Stack not found"**
- Create stack: `mise exec -- pulumi stack init dev`
- Configure: `mise exec -- pulumi config set gcp:project verity-platform-473406`