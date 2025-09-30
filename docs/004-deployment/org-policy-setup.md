# Organization Policy Configuration

## Domain Restricted Sharing Policy

The GCP organization has a Domain Restricted Sharing policy (`constraints/iam.allowedPolicyMemberDomains`) that restricts IAM member types to users from the `reallm.com` domain.

This policy blocks `allUsers` and `allAuthenticatedUsers` IAM bindings by default, which is required for:
- Public Cloud Run services
- Firebase Hosting proxy to Cloud Run
- Public API access

## Allowing allUsers for Public Services

To enable public access to Cloud Run services (required for Firebase Hosting integration), the org policy was updated to allow both the organization domain AND `allUsers`:

```yaml
constraint: constraints/iam.allowedPolicyMemberDomains
listPolicy:
  allowedValues:
  - C02ctum89  # reallm.com domain customer ID
  - allUsers
```

### Command to Apply

```bash
# Create policy file
cat > /tmp/iam-policy-exception.yaml <<EOF
constraint: constraints/iam.allowedPolicyMemberDomains
listPolicy:
  allowedValues:
  - C02ctum89
  - allUsers
EOF

# Apply at organization level (requires orgpolicy.policyAdmin role)
gcloud resource-manager org-policies set-policy /tmp/iam-policy-exception.yaml --organization=931521204724
```

### Grant Public Access to Cloud Run

After updating the org policy, grant public invoker access to the Cloud Run service:

```bash
gcloud run services add-iam-policy-binding verity-backend-dev \
  --region=europe-west1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

## Security Considerations

- **Application-level authentication**: Since Cloud Run is publicly accessible, API security is enforced via Firebase Auth JWT validation
- **Firebase Hosting as CDN**: Public requests go through Firebase Hosting CDN first, providing caching and DDoS protection
- **Rate limiting**: Consider adding Cloud Armor for additional protection if needed

## Required IAM Roles

To manage org policies, you need:
- `roles/orgpolicy.policyAdmin` - Organization Policy Administrator
- `roles/resourcemanager.organizationAdmin` - Organization Administrator (to grant policy admin)

Grant the role:
```bash
gcloud organizations add-iam-policy-binding 931521204724 \
  --member="user:YOUR_EMAIL@reallm.com" \
  --role="roles/orgpolicy.policyAdmin"
```
