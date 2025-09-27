#!/bin/bash
set -e

PROJECT_ID="verity-platform-473406"
REGION="europe-west1"
INSTANCE_NAME="verity-postgres"
DATABASE_NAME="uxr"
DATABASE_USER="uxr"

echo "Setting up Cloud SQL database for Verity..."
echo "Project: $PROJECT_ID"
echo "Instance: $INSTANCE_NAME"
echo ""

# Check authentication
echo "Current authentication:"
gcloud auth list --filter=status:ACTIVE --format="table(account,status)"

# Set the project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable sqladmin.googleapis.com --quiet

# Check if instance already exists
echo "Checking if Cloud SQL instance exists..."
if gcloud sql instances describe $INSTANCE_NAME --quiet &>/dev/null; then
    echo "✓ Instance $INSTANCE_NAME already exists"
else
    echo "Creating Cloud SQL instance: $INSTANCE_NAME"
    echo "This will take 5-10 minutes..."
    
    # Use simpler configuration for MVP
    gcloud sql instances create $INSTANCE_NAME \
      --database-version=POSTGRES_16 \
      --region=$REGION \
      --cpu=1 \
      --memory=3840MB \
      --storage-size=10GB \
      --storage-type=SSD \
      --storage-auto-increase \
      --backup-start-time=02:00 \
      --maintenance-window-day=SUN \
      --maintenance-window-hour=03 \
      --no-deletion-protection
      
    echo "✓ Instance created successfully"
fi

# Generate secure password
echo "Generating secure database password..."
DB_PASSWORD=$(openssl rand -base64 32)

# Check if user exists
echo "Checking if database user exists..."
if gcloud sql users describe $DATABASE_USER --instance=$INSTANCE_NAME --quiet &>/dev/null; then
    echo "✓ User $DATABASE_USER already exists"
    echo "⚠️  Using existing user - you may need to reset the password manually"
else
    echo "Creating database user: $DATABASE_USER"
    gcloud sql users create $DATABASE_USER \
      --instance=$INSTANCE_NAME \
      --password="$DB_PASSWORD"
    echo "✓ User created successfully"
fi

# Check if database exists
echo "Checking if database exists..."
if gcloud sql databases describe $DATABASE_NAME --instance=$INSTANCE_NAME --quiet &>/dev/null; then
    echo "✓ Database $DATABASE_NAME already exists"
else
    echo "Creating database: $DATABASE_NAME"
    gcloud sql databases create $DATABASE_NAME \
      --instance=$INSTANCE_NAME
    echo "✓ Database created successfully"
fi

# Get instance connection name
CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format="value(connectionName)")

# Grant Cloud SQL permissions to the GitHub Actions service account
echo "Granting Cloud SQL permissions to GitHub Actions service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client" \
  --quiet || echo "Permission may already exist"

echo ""
echo "✅ Database setup complete!"
echo ""
echo "📋 Database connection details:"
echo "Instance: $CONNECTION_NAME"
echo "Database: $DATABASE_NAME"
echo "User: $DATABASE_USER"
echo "Password: $DB_PASSWORD"
echo ""
echo "🔐 IMPORTANT: Store this password securely!"
echo ""
echo "📝 Next steps:"
echo "1. Set GitHub secret:"
echo "   gh secret set DATABASE_PASSWORD --body \"$DB_PASSWORD\""
echo ""
echo "2. Connection string for Cloud Run:"
echo "   postgresql+psycopg://$DATABASE_USER:[PASSWORD]@/$DATABASE_NAME?host=/cloudsql/$CONNECTION_NAME"
echo ""
echo "3. Test connection (optional):"
echo "   gcloud sql connect $INSTANCE_NAME --user=$DATABASE_USER --database=$DATABASE_NAME"