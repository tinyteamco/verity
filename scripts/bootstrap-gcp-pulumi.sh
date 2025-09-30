#!/bin/bash
# Bootstrap script for GCP + Pulumi infrastructure setup
# This script creates the foundational resources needed for IaC deployments
#
# Run this ONCE manually before setting up Pulumi in the repository
# Prerequisites: gcloud CLI installed and authenticated

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-verity-platform-473406}"
REGION="${REGION:-europe-west1}"
GITHUB_REPO="${GITHUB_REPO:-}"  # Format: "username/repo" (e.g., "jkp/verity")

echo -e "${GREEN}🚀 Verity Platform - GCP + Pulumi Bootstrap${NC}"
echo "=================================================="
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI not found${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}❌ Error: Not authenticated with gcloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

# Check if GitHub repo is provided (needed for Workload Identity)
if [ -z "$GITHUB_REPO" ]; then
    echo -e "${YELLOW}⚠️  Warning: GITHUB_REPO not set${NC}"
    echo "Workload Identity Federation will not be configured"
    echo "Set it with: export GITHUB_REPO='username/repo'"
    echo ""
    read -p "Continue without Workload Identity? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    SKIP_WORKLOAD_IDENTITY=true
else
    SKIP_WORKLOAD_IDENTITY=false
fi

# Set project
echo -e "${GREEN}📋 Setting active project...${NC}"
gcloud config set project "$PROJECT_ID"

# Get project number (needed for Workload Identity)
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
echo "Project number: $PROJECT_NUMBER"
echo ""

# Enable required APIs
echo -e "${GREEN}🔌 Enabling required GCP APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    sql-component.googleapis.com \
    secretmanager.googleapis.com \
    iam.googleapis.com \
    iamcredentials.googleapis.com \
    cloudresourcemanager.googleapis.com \
    compute.googleapis.com \
    servicenetworking.googleapis.com

echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# Create service account for Pulumi deployments
SA_NAME="pulumi-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${GREEN}🔐 Creating service account: $SA_EMAIL${NC}"

if gcloud iam service-accounts describe "$SA_EMAIL" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Service account already exists${NC}"
else
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="Pulumi Infrastructure Deployer" \
        --description="Service account for CI/CD infrastructure deployments via Pulumi"
    echo -e "${GREEN}✅ Service account created${NC}"
fi
echo ""

# Grant necessary IAM roles
echo -e "${GREEN}🔑 Granting IAM roles to service account...${NC}"

ROLES=(
    "roles/editor"                              # Create/modify most resources
    "roles/iam.serviceAccountAdmin"             # Create service accounts
    "roles/resourcemanager.projectIamAdmin"     # Grant IAM permissions
    "roles/cloudsql.admin"                      # Manage Cloud SQL
    "roles/run.admin"                           # Manage Cloud Run
    "roles/secretmanager.admin"                 # Manage secrets
)

for ROLE in "${ROLES[@]}"; do
    echo "  Granting $ROLE..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$ROLE" \
        --condition=None \
        > /dev/null 2>&1
done

echo -e "${GREEN}✅ IAM roles granted${NC}"
echo ""

# Set up Workload Identity Federation (if GitHub repo provided)
if [ "$SKIP_WORKLOAD_IDENTITY" = false ]; then
    echo -e "${GREEN}🔗 Setting up Workload Identity Federation for GitHub Actions...${NC}"

    POOL_NAME="github"
    PROVIDER_NAME="github"

    # Create workload identity pool
    if gcloud iam workload-identity-pools describe "$POOL_NAME" --location=global &> /dev/null; then
        echo -e "${YELLOW}⚠️  Workload Identity Pool already exists${NC}"
    else
        gcloud iam workload-identity-pools create "$POOL_NAME" \
            --location=global \
            --display-name="GitHub Actions Pool" \
            --description="Identity pool for GitHub Actions workflows"
        echo -e "${GREEN}✅ Workload Identity Pool created${NC}"
    fi

    # Create OIDC provider
    if gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
        --workload-identity-pool="$POOL_NAME" \
        --location=global &> /dev/null; then
        echo -e "${YELLOW}⚠️  OIDC provider already exists${NC}"
    else
        GITHUB_OWNER=$(echo "$GITHUB_REPO" | cut -d'/' -f1)

        gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
            --location=global \
            --workload-identity-pool="$POOL_NAME" \
            --display-name="GitHub OIDC Provider" \
            --issuer-uri="https://token.actions.githubusercontent.com" \
            --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
            --attribute-condition="assertion.repository_owner=='${GITHUB_OWNER}'"
        echo -e "${GREEN}✅ OIDC provider created${NC}"
    fi

    # Bind service account to GitHub repository
    echo "  Binding service account to GitHub repository: $GITHUB_REPO"
    gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
        --role=roles/iam.workloadIdentityUser \
        --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${GITHUB_REPO}" \
        > /dev/null 2>&1

    echo -e "${GREEN}✅ Workload Identity configured${NC}"
    echo ""
fi

# Summary
echo ""
echo "=================================================="
echo -e "${GREEN}✅ Bootstrap Complete!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Create Pulumi Cloud account at https://app.pulumi.com"
echo "2. Generate access token: Settings → Access Tokens"
echo "3. Add to GitHub secrets:"
echo "   - Go to: https://github.com/$GITHUB_REPO/settings/secrets/actions"
echo "   - New secret: PULUMI_ACCESS_TOKEN"
echo ""

if [ "$SKIP_WORKLOAD_IDENTITY" = false ]; then
    echo "4. Add these values to your GitHub Actions workflow:"
    echo ""
    echo "   workload_identity_provider: projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github/providers/github"
    echo "   service_account: ${SA_EMAIL}"
    echo ""
else
    echo "4. (Optional) Download service account key for local testing:"
    echo ""
    echo "   gcloud iam service-accounts keys create pulumi-deployer-key.json \\"
    echo "     --iam-account=${SA_EMAIL}"
    echo ""
    echo "   ⚠️  Keep this key secure! Add to .gitignore"
    echo ""
fi

echo "5. Set up Pulumi project in /infra directory"
echo "6. Create deploy-infra.yml workflow"
echo ""
echo -e "${YELLOW}📝 Save these values for reference:${NC}"
echo "   PROJECT_ID=$PROJECT_ID"
echo "   PROJECT_NUMBER=$PROJECT_NUMBER"
echo "   REGION=$REGION"
echo "   SERVICE_ACCOUNT=$SA_EMAIL"
echo ""
echo "Happy infrastructure coding! 🚀"