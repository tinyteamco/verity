# Security Guidelines

## Multi-Tenancy Security Principles

### Golden Rule: Never Trust Client-Provided Tenant Context

**NEVER use client-provided headers, query parameters, or request body fields to determine which tenant/organization a user can access.**

### ❌ INSECURE PATTERNS

```python
# WRONG: Trusting client-provided header
@app.get("/orgs/{org_id}/resources")
def get_resources(
    org_id: int,
    org_header: str = Header(..., alias="X-Organization-ID"),  # ❌ Client-controlled!
):
    # Backend filters by header instead of verifying user belongs to path org_id
    resources = db.query(Resource).filter(Resource.org_id == org_header).all()
    return resources
```

**Attack**: Client can set `X-Organization-ID: 999` in header and access any org's data.

```python
# WRONG: Trusting request body for org context
@app.post("/resources")
def create_resource(data: dict):
    org_id = data["org_id"]  # ❌ Client-controlled!
    resource = Resource(org_id=org_id, **data)
    db.add(resource)
    return resource
```

**Attack**: Client can create resources in any organization by changing `org_id` in JSON body.

### ✅ SECURE PATTERNS

#### Pattern 1: Path-Based with Permission Check

```python
@app.get("/orgs/{org_id}/resources")
def get_resources(
    org_id: int,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    # Verify user belongs to this org (or is super_admin)
    if not current_user.is_super_admin:
        user_in_org = db.query(User).filter(
            User.firebase_uid == current_user.firebase_uid,
            User.organization_id == org_id
        ).first()
        if not user_in_org:
            raise HTTPException(status_code=403, detail="User not in organization")

    # Now safe to query by org_id from path
    resources = db.query(Resource).filter(Resource.org_id == org_id).all()
    return resources
```

**Security**: Backend verifies user belongs to the org before returning data.

#### Pattern 2: Resource-Based with Implicit Org Check

```python
@app.get("/resources/{resource_id}")
def get_resource(
    resource_id: int,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    # Get user's org from database (server-side source of truth)
    if current_user.is_super_admin:
        # Super admin can access any resource
        resource = db.query(Resource).filter(Resource.id == resource_id).first()
    else:
        user = db.query(User).filter(
            User.firebase_uid == current_user.firebase_uid
        ).first()
        if not user:
            raise HTTPException(status_code=403, detail="User not found")

        # Only return resource if it belongs to user's org
        resource = db.query(Resource).filter(
            Resource.id == resource_id,
            Resource.org_id == user.organization_id  # Server-side org check
        ).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource
```

**Security**: User's org is retrieved from database, resource must belong to that org.

#### Pattern 3: User-Scoped (No Org Leakage)

```python
@app.post("/resources")
def create_resource(
    data: ResourceCreate,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    # Get org from current user's database record
    user = db.query(User).filter(
        User.firebase_uid == current_user.firebase_uid
    ).first()
    if not user:
        raise HTTPException(status_code=403, detail="User not found")

    # Server determines org_id, not client
    resource = Resource(
        org_id=user.organization_id,  # ✅ Server-controlled!
        **data.model_dump()
    )
    db.add(resource)
    db.commit()
    return resource
```

**Security**: Organization is determined by server based on authenticated user, not client input.

## Authentication vs Authorization

### Authentication: "Who are you?"
- Verify JWT token signature
- Extract user identity (firebase_uid, email)
- Verify token hasn't expired

### Authorization: "What can you access?"
- Check user belongs to organization (database lookup)
- Verify user role has required permissions
- Confirm resource belongs to user's organization

### ❌ Common Mistake: Authentication without Authorization

```python
# WRONG: Only checking authentication
@app.get("/orgs/{org_id}/data")
def get_data(
    org_id: int,
    current_user: Annotated[AuthUser, Depends(get_current_user)],  # ✅ Authenticated
    db: Annotated[Session, Depends(get_db)],
):
    # ❌ No authorization check - any authenticated user can access any org!
    return db.query(Data).filter(Data.org_id == org_id).all()
```

**Attack**: User from Org A can access Org B's data by changing URL: `/orgs/2/data`

```python
# CORRECT: Authentication + Authorization
@app.get("/orgs/{org_id}/data")
def get_data(
    org_id: int,
    current_user: Annotated[AuthUser, Depends(get_current_user)],  # ✅ Authenticated
    db: Annotated[Session, Depends(get_db)],
):
    # ✅ Authorization: verify user can access this org
    if not current_user.is_super_admin:
        user_in_org = db.query(User).filter(
            User.firebase_uid == current_user.firebase_uid,
            User.organization_id == org_id
        ).first()
        if not user_in_org:
            raise HTTPException(status_code=403, detail="Forbidden")

    return db.query(Data).filter(Data.org_id == org_id).all()
```

## Pre-Deployment Security Checklist

Before deploying ANY endpoint that touches organization-scoped data:

- [ ] Endpoint gets user identity from JWT token (not client input)
- [ ] Endpoint verifies user belongs to target organization (database lookup)
- [ ] No client-provided headers/params are used for authorization
- [ ] Resource queries include org_id filter matching user's org
- [ ] Tests include cross-organization access attempts (should fail with 403)
- [ ] Super admin access is explicitly handled (if applicable)

## Testing Requirements

Every multi-tenant endpoint MUST have tests for:

1. ✅ **Happy path**: User can access their own org's resources
2. ❌ **Cross-org denial**: User from Org A CANNOT access Org B's resources (403)
3. ❌ **Unauthenticated denial**: Requests without token are rejected (401)
4. ✅ **Super admin god-mode**: Super admin can access any org (if applicable)

Example test:

```python
def test_cannot_access_other_org_resources():
    # Create user in Org 1
    user1_token = create_user(org_id=1)

    # Create resource in Org 2
    resource_id = create_resource(org_id=2)

    # User from Org 1 tries to access Org 2's resource
    response = client.get(
        f"/orgs/2/resources/{resource_id}",
        headers={"Authorization": f"Bearer {user1_token}"}
    )

    assert response.status_code == 403
    assert "not in organization" in response.json()["detail"].lower()
```

## Code Review Red Flags

🚨 **STOP and review carefully if you see:**

- `Header(..., alias="X-Organization-ID")` or any custom org/tenant header
- `org_id = data["org_id"]` from request body for authorization
- `org_id: int = Query(...)` for access control
- Missing authorization check after authentication
- Queries that don't filter by user's organization
- Endpoints that trust client-provided tenant context

## Super Admin Special Cases

Super admins have "god-mode" access to all organizations:

```python
if current_user.is_super_admin:
    # Super admin can access any org - no further checks needed
    resources = db.query(Resource).filter(Resource.org_id == org_id).all()
else:
    # Regular user - verify org membership
    user_in_org = db.query(User).filter(
        User.firebase_uid == current_user.firebase_uid,
        User.organization_id == org_id
    ).first()
    if not user_in_org:
        raise HTTPException(status_code=403, detail="Forbidden")
    resources = db.query(Resource).filter(Resource.org_id == org_id).all()
```

## Summary

**The vulnerability that caused production data leakage:**
- Routes were `/orgs/{org_id}/studies`
- Backend trusted `X-Organization-ID` header from client
- Client could access any org by changing header value

**The fix:**
- Remove all client-provided tenant context headers
- Use path parameters with server-side permission verification
- Query database to confirm user belongs to target organization

**Prevention going forward:**
- Never trust client input for authorization
- Always verify org membership server-side
- Test cross-org access denial
- Review all endpoints for authorization checks
