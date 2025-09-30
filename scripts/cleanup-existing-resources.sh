#!/bin/bash
# Cleanup existing manually-created GCP resources
# This prepares the project for fresh Pulumi-managed infrastructure
#
# IMPORTANT: This will DELETE resources. Make sure you have backups if needed!

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ID="${PROJECT_ID:-verity-platform-473406}"
REGION="${REGION:-europe-west1}"

echo -e "${YELLOW}⚠️  WARNING: Resource Cleanup${NC}"
echo "=================================================="
echo ""
echo "This will DELETE the following resources:"
echo "  - Cloud Run service: verity-backend"
echo "  - Cloud SQL instance: verity-postgres (and all data!)"
echo ""
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Confirmation
read -p "Are you sure you want to delete these resources? (type 'DELETE' to confirm): " CONFIRM
if [ "$CONFIRM" != "DELETE" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo -e "${YELLOW}Second confirmation - this is irreversible!${NC}"
read -p "Type the project ID to confirm: " CONFIRM_PROJECT
if [ "$CONFIRM_PROJECT" != "$PROJECT_ID" ]; then
    echo "Project ID mismatch. Aborted."
    exit 1
fi

echo ""
gcloud config set project "$PROJECT_ID"

# =============================================================================
# 1. Delete Cloud Run service
# =============================================================================

echo ""
echo -e "${GREEN}🗑️  Deleting Cloud Run service: verity-backend${NC}"

if gcloud run services describe verity-backend --region="$REGION" &>/dev/null; then
    gcloud run services delete verity-backend \
        --region="$REGION" \
        --quiet
    echo -e "${GREEN}✅ Cloud Run service deleted${NC}"
else
    echo -e "${YELLOW}⚠️  Cloud Run service not found (already deleted?)${NC}"
fi

# =============================================================================
# 2. Delete Cloud SQL instance
# =============================================================================

echo ""
echo -e "${GREEN}🗑️  Deleting Cloud SQL instance: verity-postgres${NC}"
echo -e "${YELLOW}⏳ This will take 5-10 minutes...${NC}"

if gcloud sql instances describe verity-postgres &>/dev/null; then
    # Disable deletion protection first (if enabled)
    echo "  Disabling deletion protection..."
    gcloud sql instances patch verity-postgres \
        --no-deletion-protection \
        --quiet || true

    # Delete the instance
    gcloud sql instances delete verity-postgres \
        --quiet

    echo -e "${GREEN}✅ Cloud SQL instance deleted${NC}"
else
    echo -e "${YELLOW}⚠️  Cloud SQL instance not found (already deleted?)${NC}"
fi

# =============================================================================
# 3. Optional: Clean up VPC connectors (if any)
# =============================================================================

echo ""
echo -e "${GREEN}🔍 Checking for VPC connectors...${NC}"

CONNECTORS=$(gcloud compute networks vpc-access connectors list \
    --region="$REGION" \
    --format="value(name)" 2>/dev/null || echo "")

if [ -n "$CONNECTORS" ]; then
    echo "Found VPC connectors:"
    echo "$CONNECTORS"
    read -p "Delete VPC connectors? (y/N): " DELETE_CONNECTORS

    if [[ $DELETE_CONNECTORS =~ ^[Yy]$ ]]; then
        for CONNECTOR in $CONNECTORS; do
            echo "  Deleting $CONNECTOR..."
            gcloud compute networks vpc-access connectors delete "$CONNECTOR" \
                --region="$REGION" \
                --quiet
        done
        echo -e "${GREEN}✅ VPC connectors deleted${NC}"
    fi
else
    echo "No VPC connectors found"
fi

# =============================================================================
# 4. Optional: Clean up secrets (if any)
# =============================================================================

echo ""
echo -e "${GREEN}🔍 Checking for secrets...${NC}"

SECRETS=$(gcloud secrets list --format="value(name)" 2>/dev/null | grep -i verity || echo "")

if [ -n "$SECRETS" ]; then
    echo "Found secrets:"
    echo "$SECRETS"
    read -p "Delete secrets? (y/N): " DELETE_SECRETS

    if [[ $DELETE_SECRETS =~ ^[Yy]$ ]]; then
        for SECRET in $SECRETS; do
            echo "  Deleting $SECRET..."
            gcloud secrets delete "$SECRET" --quiet
        done
        echo -e "${GREEN}✅ Secrets deleted${NC}"
    fi
else
    echo "No secrets found"
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Cleanup Complete!${NC}"
echo "=================================================="
echo ""
echo "Deleted resources:"
echo "  ✅ Cloud Run service: verity-backend"
echo "  ✅ Cloud SQL instance: verity-postgres"
echo ""
echo "The project is now ready for fresh Pulumi deployment."
echo ""
echo "Next steps:"
echo "  1. Set up Pulumi Cloud (if not done): https://app.pulumi.com"
echo "  2. Add PULUMI_ACCESS_TOKEN to GitHub secrets"
echo "  3. Run: GitHub Actions → Deploy Infrastructure → dev → preview"
echo "  4. Review preview, then run with 'up' action"
echo ""
echo "Pulumi will create:"
echo "  - verity-db-dev (Cloud SQL with proper security)"
echo "  - verity-backend-dev (Cloud Run)"
echo "  - Custom service accounts (not default compute SA)"
echo "  - Private networking (no public IPs)"
echo ""