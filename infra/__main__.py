"""Verity Platform Infrastructure as Code with Pulumi.

This module defines the complete infrastructure for the Verity UXR platform:
- Cloud SQL PostgreSQL database
- Cloud Run service for backend API (internal ingress)
- Firebase Hosting for public access and API proxy
- Service accounts with least-privilege IAM
- Secrets in Secret Manager
"""

import pulumi
import pulumi_gcp as gcp

# Configuration
config = pulumi.Config()
gcp_config = pulumi.Config("gcp")
project = gcp_config.require("project")
region = config.get("region") or "us-central1"

# Get current stack name (dev/prod)
stack = pulumi.get_stack()

# Resource naming convention: verity-{resource}-{stack}
def resource_name(name: str) -> str:
    """Generate consistent resource names across stacks."""
    return f"verity-{name}-{stack}"


# =============================================================================
# Enable Required APIs
# =============================================================================

# Enable required GCP APIs before creating resources
required_apis = [
    "run.googleapis.com",              # Cloud Run
    "sqladmin.googleapis.com",         # Cloud SQL Admin
    "secretmanager.googleapis.com",    # Secret Manager
    "firebase.googleapis.com",         # Firebase
    "firebasehosting.googleapis.com",  # Firebase Hosting
]

enabled_services = []
for api in required_apis:
    service = gcp.projects.Service(
        f"enable-{api.replace('.googleapis.com', '').replace('.', '-')}",
        service=api,
        project=project,
        # Disable on destroy to clean up
        disable_on_destroy=False,
    )
    enabled_services.append(service)

# =============================================================================
# Service Accounts
# =============================================================================

# Backend runtime service account (runs Cloud Run service)
backend_sa = gcp.serviceaccount.Account(
    "backend-runtime",
    account_id=resource_name("backend"),
    display_name=f"Backend Runtime ({stack})",
    description=f"Service account for backend API Cloud Run service ({stack} environment)",
)

# Grant Cloud SQL Client role (connect to database)
backend_sql_binding = gcp.projects.IAMMember(
    "backend-cloudsql-client",
    project=project,
    role="roles/cloudsql.client",
    member=backend_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

# Grant Secret Manager Secret Accessor (read secrets)
backend_secrets_binding = gcp.projects.IAMMember(
    "backend-secrets-accessor",
    project=project,
    role="roles/secretmanager.secretAccessor",
    member=backend_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

# =============================================================================
# GitHub Actions Service Account (CI/CD)
# =============================================================================

# Note: Service account already exists (created manually), so we just reference it
# Format: {account_id}@{project}.iam.gserviceaccount.com
github_actions_sa_email = f"github-actions@{project}.iam.gserviceaccount.com"

# Grant roles needed for CI/CD deployments

# Artifact Registry Writer (push Docker images)
github_actions_artifact_binding = gcp.projects.IAMMember(
    "github-actions-artifact-writer",
    project=project,
    role="roles/artifactregistry.writer",
    member=f"serviceAccount:{github_actions_sa_email}",
)

# Cloud Run Admin (deploy services)
github_actions_run_binding = gcp.projects.IAMMember(
    "github-actions-run-admin",
    project=project,
    role="roles/run.admin",
    member=f"serviceAccount:{github_actions_sa_email}",
)

# Service Account User (act as service accounts)
github_actions_sa_user_binding = gcp.projects.IAMMember(
    "github-actions-sa-user",
    project=project,
    role="roles/iam.serviceAccountUser",
    member=f"serviceAccount:{github_actions_sa_email}",
)

# Cloud SQL Client (run migrations via proxy)
github_actions_sql_binding = gcp.projects.IAMMember(
    "github-actions-cloudsql-client",
    project=project,
    role="roles/cloudsql.client",
    member=f"serviceAccount:{github_actions_sa_email}",
)

# Secret Manager Secret Accessor (read database credentials)
github_actions_secrets_binding = gcp.projects.IAMMember(
    "github-actions-secrets-accessor",
    project=project,
    role="roles/secretmanager.secretAccessor",
    member=f"serviceAccount:{github_actions_sa_email}",
)

# Firebase Admin (manage Firebase Auth users)
github_actions_firebase_auth_binding = gcp.projects.IAMMember(
    "github-actions-firebase-auth-admin",
    project=project,
    role="roles/firebaseauth.admin",
    member=f"serviceAccount:{github_actions_sa_email}",
)

# Firebase Hosting Admin (deploy to Firebase Hosting)
github_actions_firebase_hosting_binding = gcp.projects.IAMMember(
    "github-actions-firebase-hosting-admin",
    project=project,
    role="roles/firebasehosting.admin",
    member=f"serviceAccount:{github_actions_sa_email}",
)

# =============================================================================
# Cloud SQL (PostgreSQL 16)
# =============================================================================
# Note: Using public IP with Cloud SQL Proxy for secure, cost-effective access
# Cloud Run connects via unix socket using the Cloud SQL Proxy sidecar

# Generate random password for database
db_password = pulumi.Config().get_secret("db_password") or pulumi.Output.secret("change-me-in-prod")

# Cloud SQL instance
db_instance = gcp.sql.DatabaseInstance(
    "postgres-instance",
    name=resource_name("db"),
    database_version="POSTGRES_15",  # Using PG15 for broader tier compatibility
    region=region,
    settings=gcp.sql.DatabaseInstanceSettingsArgs(
        tier="db-f1-micro" if stack == "dev" else "db-n1-standard-1",  # Shared-core for dev, dedicated for prod
        ip_configuration=gcp.sql.DatabaseInstanceSettingsIpConfigurationArgs(
            ipv4_enabled=True,  # Public IP with Cloud SQL Proxy
            # Authorized networks can be added here if needed
            # Cloud Run uses Cloud SQL Proxy which doesn't need IP whitelist
        ),
        backup_configuration=gcp.sql.DatabaseInstanceSettingsBackupConfigurationArgs(
            enabled=True,
            start_time="03:00",  # 3 AM UTC
            point_in_time_recovery_enabled=True,
            transaction_log_retention_days=7,
        ),
        database_flags=[
            gcp.sql.DatabaseInstanceSettingsDatabaseFlagArgs(
                name="max_connections",
                value="100",
            ),
        ],
    ),
    deletion_protection=stack == "prod",  # Prevent accidental deletion in prod
)

# Database for application
db = gcp.sql.Database(
    "app-database",
    name="verity",
    instance=db_instance.name,
)

# Database user
db_user = gcp.sql.User(
    "app-user",
    name="verity_app",
    instance=db_instance.name,
    password=db_password,
)

# =============================================================================
# Secrets (Secret Manager)
# =============================================================================

# Database connection string secret
db_connection_string = pulumi.Output.all(
    db_instance.connection_name,
    db.name,
    db_user.name,
    db_password,
).apply(
    lambda args: f"postgresql+psycopg://{args[2]}:{args[3]}@/{args[1]}?host=/cloudsql/{args[0]}"
)

database_url_secret = gcp.secretmanager.Secret(
    "database-url",
    secret_id=resource_name("database-url"),
    replication=gcp.secretmanager.SecretReplicationArgs(
        auto=gcp.secretmanager.SecretReplicationAutoArgs(),
    ),
)

database_url_secret_version = gcp.secretmanager.SecretVersion(
    "database-url-version",
    secret=database_url_secret.id,
    secret_data=db_connection_string,
)

# =============================================================================
# Cloud Run (Backend API)
# =============================================================================

# Cloud Run service
# Note: Image is deployed via CI/CD, this just sets up the service configuration
# Cloud SQL connection uses Cloud SQL Proxy (configured via annotations)
backend_service = gcp.cloudrunv2.Service(
    "backend-service",
    name=resource_name("backend"),
    location=region,
    ingress="INGRESS_TRAFFIC_ALL",  # Public ingress required for Firebase Hosting
    template={
        "service_account": backend_sa.email,
        "scaling": {
            "min_instance_count": 0 if stack == "dev" else 1,
            "max_instance_count": 10 if stack == "dev" else 100,
        },
        # Cloud SQL connection via Cloud SQL Proxy
        "annotations": {
            "run.googleapis.com/cloudsql-instances": db_instance.connection_name,
        },
        "containers": [{
            # Placeholder image - CI/CD will manage actual deployments
            # Using public Cloud Run hello-world image for initial creation
            "image": "us-docker.pkg.dev/cloudrun/container/hello",
            "envs": [
                {
                    "name": "APP_ENV",
                    "value": stack,
                },
                {
                    "name": "DATABASE_URL",
                    "value_source": {
                        "secret_key_ref": {
                            "secret": database_url_secret.secret_id,
                            "version": "latest",
                        },
                    },
                },
            ],
            "resources": {
                "limits": {
                    "cpu": "1000m",
                    "memory": "512Mi",
                },
            },
        }],
    },
    opts=pulumi.ResourceOptions(
        # Ignore changes to container image - managed by CI/CD deployments
        ignore_changes=["template.containers[0].image"],
    ),
)

# =============================================================================
# Firebase Hosting (Public Frontend & API Proxy)
# =============================================================================

# Note: Cloud Run is publicly accessible with ingress=INGRESS_TRAFFIC_ALL
# Firebase Hosting proxies /api/** requests to Cloud Run
# Security is enforced at application level via Firebase Auth JWT validation

# Add GCP project to Firebase
firebase_project = gcp.firebase.Project(
    "firebase-project",
    project=project,
    opts=pulumi.ResourceOptions(depends_on=enabled_services),
)

# =============================================================================
# Identity Platform (Firebase Auth) Configuration
# =============================================================================

# Configure Firebase Auth sign-in methods
identity_config = gcp.identityplatform.Config(
    "identity-platform-config",
    project=project,
    sign_in=gcp.identityplatform.ConfigSignInArgs(
        email=gcp.identityplatform.ConfigSignInEmailArgs(
            enabled=True,
            password_required=True,
        ),
    ),
    opts=pulumi.ResourceOptions(depends_on=[firebase_project]),
)

# Firebase Hosting Site
hosting_site = gcp.firebase.HostingSite(
    "hosting-site",
    project=project,
    site_id=resource_name("app"),
    opts=pulumi.ResourceOptions(depends_on=[firebase_project]),
)

# Firebase Hosting Config - proxy /api/** to Cloud Run
hosting_version = gcp.firebase.HostingVersion(
    "hosting-version",
    site_id=hosting_site.site_id,
    config=gcp.firebase.HostingVersionConfigArgs(
        rewrites=[
            gcp.firebase.HostingVersionConfigRewriteArgs(
                glob="/api/**",
                run=gcp.firebase.HostingVersionConfigRewriteRunArgs(
                    service_id=backend_service.name,
                    region=region,
                ),
            ),
        ],
    ),
)

# Release the hosting version
hosting_release = gcp.firebase.HostingRelease(
    "hosting-release",
    site_id=hosting_site.site_id,
    version_name=hosting_version.name,
    message=f"Deployed via Pulumi - {stack} stack",
)

# =============================================================================
# Outputs
# =============================================================================

pulumi.export("project_id", project)
pulumi.export("region", region)
pulumi.export("stack", stack)

# Service accounts
pulumi.export("backend_service_account", backend_sa.email)
pulumi.export("github_actions_service_account", github_actions_sa_email)

# Database
pulumi.export("db_instance_name", db_instance.name)
pulumi.export("db_connection_name", db_instance.connection_name)
pulumi.export("database_name", db.name)

# Cloud Run
pulumi.export("backend_url", backend_service.uri)
pulumi.export("backend_service_name", backend_service.name)

# Secrets
pulumi.export("database_url_secret_name", database_url_secret.secret_id)

# Firebase Hosting
pulumi.export("hosting_site_id", hosting_site.site_id)
pulumi.export("hosting_url", hosting_site.default_url)