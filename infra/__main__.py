"""Verity Platform Infrastructure as Code with Pulumi.

This module defines the complete infrastructure for the Verity UXR platform:
- Cloud SQL PostgreSQL database
- Cloud Run service for backend API
- Service accounts with least-privilege IAM
- Secrets in Secret Manager
- VPC networking for private connectivity
"""

import pulumi
import pulumi_gcp as gcp

# Configuration
config = pulumi.Config()
project = config.require("gcp:project")
region = config.get("region") or "us-central1"

# Get current stack name (dev/prod)
stack = pulumi.get_stack()

# Resource naming convention: verity-{resource}-{stack}
def resource_name(name: str) -> str:
    """Generate consistent resource names across stacks."""
    return f"verity-{name}-{stack}"


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
# Networking (for Cloud SQL private IP)
# =============================================================================

# Enable VPC access (required for Cloud SQL private IP)
# Note: Using default VPC for simplicity, can create custom VPC later
vpc_network = gcp.compute.Network(
    "vpc-network",
    name=resource_name("vpc"),
    auto_create_subnetworks=True,
    description=f"VPC network for Verity platform ({stack})",
)

# Allocate IP range for Google services (Cloud SQL, etc.)
private_ip_range = gcp.compute.GlobalAddress(
    "private-ip-range",
    name=resource_name("private-ip"),
    purpose="VPC_PEERING",
    address_type="INTERNAL",
    prefix_length=16,
    network=vpc_network.id,
)

# Create private VPC connection for Cloud SQL
private_vpc_connection = gcp.servicenetworking.Connection(
    "private-vpc-connection",
    network=vpc_network.id,
    service="servicenetworking.googleapis.com",
    reserved_peering_ranges=[private_ip_range.name],
)

# =============================================================================
# Cloud SQL (PostgreSQL 16)
# =============================================================================

# Generate random password for database
db_password = pulumi.Config().get_secret("db_password") or pulumi.Output.secret("change-me-in-prod")

# Cloud SQL instance
db_instance = gcp.sql.DatabaseInstance(
    "postgres-instance",
    name=resource_name("db"),
    database_version="POSTGRES_16",
    region=region,
    settings=gcp.sql.DatabaseInstanceSettingsArgs(
        tier="db-f1-micro" if stack == "dev" else "db-n1-standard-1",
        ip_configuration=gcp.sql.DatabaseInstanceSettingsIpConfigurationArgs(
            ipv4_enabled=False,  # Private IP only
            private_network=vpc_network.id,
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
    opts=pulumi.ResourceOptions(depends_on=[private_vpc_connection]),
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

# VPC connector for Cloud Run to access Cloud SQL
vpc_connector = gcp.vpcaccess.Connector(
    "vpc-connector",
    name=resource_name("vpc-conn"),
    region=region,
    network=vpc_network.name,
    ip_cidr_range="10.8.0.0/28",  # Small range for connector
    min_instances=stack == "prod" and 2 or 0,
    max_instances=3,
)

# Cloud Run service
# Note: Image is deployed via CI/CD, this just sets up the service configuration
backend_service = gcp.cloudrunv2.Service(
    "backend-service",
    name=resource_name("backend"),
    location=region,
    template=gcp.cloudrunv2.ServiceTemplateArgs(
        service_account=backend_sa.email,
        scaling=gcp.cloudrunv2.ServiceTemplateScalingArgs(
            min_instance_count=0 if stack == "dev" else 1,
            max_instance_count=10 if stack == "dev" else 100,
        ),
        vpc_access=gcp.cloudrunv2.ServiceTemplateVpcAccessArgs(
            connector=vpc_connector.id,
            egress="PRIVATE_RANGES_ONLY",
        ),
        containers=[
            gcp.cloudrunv2.ServiceTemplateContainerArgs(
                # Placeholder image, CI/CD will update this
                image=f"{region}-docker.pkg.dev/{project}/verity/backend:latest",
                ports=[
                    gcp.cloudrunv2.ServiceTemplateContainerPortArgs(
                        container_port=8000,
                    ),
                ],
                envs=[
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="APP_ENV",
                        value=stack,
                    ),
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="DATABASE_URL",
                        value_source=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                            secret_key_ref=gcp.cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                secret=database_url_secret.secret_id,
                                version="latest",
                            ),
                        ),
                    ),
                ],
                resources=gcp.cloudrunv2.ServiceTemplateContainerResourcesArgs(
                    limits={
                        "cpu": "1000m",
                        "memory": "512Mi",
                    },
                ),
            )
        ],
    ),
)

# Allow unauthenticated access (for public interview links)
# TODO: Consider Cloud Armor for rate limiting and DDoS protection
backend_iam = gcp.cloudrunv2.ServiceIamMember(
    "backend-public-access",
    location=backend_service.location,
    name=backend_service.name,
    role="roles/run.invoker",
    member="allUsers",
)

# =============================================================================
# Outputs
# =============================================================================

pulumi.export("project_id", project)
pulumi.export("region", region)
pulumi.export("stack", stack)

# Service accounts
pulumi.export("backend_service_account", backend_sa.email)

# Database
pulumi.export("db_instance_name", db_instance.name)
pulumi.export("db_connection_name", db_instance.connection_name)
pulumi.export("database_name", db.name)

# Cloud Run
pulumi.export("backend_url", backend_service.uri)
pulumi.export("backend_service_name", backend_service.name)

# Secrets
pulumi.export("database_url_secret_name", database_url_secret.secret_id)