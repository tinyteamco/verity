#!/bin/bash
set -e

PROJECT_ID="verity-platform-473406"
REGION="europe-west1"
INSTANCE_NAME="verity-postgres"
DATABASE_NAME="uxr"
DATABASE_USER="uxr"

echo "Setting up Cloud SQL database for Verity..."

# Set the project
gcloud config set project $PROJECT_ID

# Enable Cloud SQL API
echo "Enabling Cloud SQL API..."
gcloud services enable sqladmin.googleapis.com

# Create Cloud SQL PostgreSQL instance with compatible tier
echo "Creating Cloud SQL instance: $INSTANCE_NAME"
gcloud sql instances create $INSTANCE_NAME \
  --database-version=POSTGRES_16 \
  --region=$REGION \
  --tier=db-perf-optimized-N-2 || echo "Instance may already exist"

# Generate secure password
echo "Generating secure database password..."
DB_PASSWORD=$(openssl rand -base64 32)

# Create database user with generated password
echo "Creating database user: $DATABASE_USER"
gcloud sql users create $DATABASE_USER \
  --instance=$INSTANCE_NAME \
  --password="$DB_PASSWORD" || echo "User may already exist"

# Create database
echo "Creating database: $DATABASE_NAME"
gcloud sql databases create $DATABASE_NAME \
  --instance=$INSTANCE_NAME || echo "Database may already exist"

# Grant Cloud SQL permissions to the GitHub Actions service account
echo "Granting Cloud SQL permissions to GitHub Actions service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

echo ""
echo "✅ Database setup complete!"
echo ""
echo "Database connection details:"
echo "Instance: $PROJECT_ID:$REGION:$INSTANCE_NAME"
echo "Database: $DATABASE_NAME"
echo "User: $DATABASE_USER"
echo "Password: $DB_PASSWORD"
echo ""
echo "⚠️  IMPORTANT: Store this password securely!"
echo "GitHub secret setup:"
echo "gh secret set DATABASE_PASSWORD --body \"$DB_PASSWORD\""
echo ""
echo "Connection string for Cloud Run:"
echo "postgresql+psycopg://$DATABASE_USER:[PASSWORD]@/$DATABASE_NAME?host=/cloudsql/$PROJECT_ID:$REGION:$INSTANCE_NAME"