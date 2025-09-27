#!/bin/bash
set -e

PROJECT_ID="verity-platform-473406"
REGION="europe-west1"
REPOSITORY_NAME="verity"
SERVICE_ACCOUNT_NAME="github-actions"

echo "Setting up Google Cloud for Verity deployment..."

# Set the project
echo "Setting project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com

# Create Artifact Registry repository
echo "Creating Artifact Registry repository: $REPOSITORY_NAME"
gcloud artifacts repositories create $REPOSITORY_NAME \
  --repository-format=docker \
  --location=$REGION \
  --description="Docker images for Verity platform" || echo "Repository may already exist"

# Create service account
echo "Creating service account: $SERVICE_ACCOUNT_NAME"
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --display-name="GitHub Actions Service Account" \
  --description="Service account for GitHub Actions deployment" || echo "Service account may already exist"

# Grant necessary permissions
echo "Granting permissions to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download service account key
echo "Creating service account key..."
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Add the contents of github-actions-key.json as a GitHub secret named 'GCP_SA_KEY'"
echo "2. Delete the local key file: rm github-actions-key.json"
echo ""
echo "GitHub secret setup:"
echo "gh secret set GCP_SA_KEY < github-actions-key.json"