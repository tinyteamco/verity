# Auth & Tenancy Notes (MVP)



- **Firebase project:** single project, two **Auth tenants**: `organization`, `interviewee`.

- **Client:** set `auth.tenantId` **before** sign-in to route to the correct tenant.

- **Backend:** verify ID token; read `claims['firebase']['tenant']` to gate routes.

- **DB mapping:** store `(firebase_uid, tenant)` per user; organization users live in `organization_users`, interviewees in `interviewees` tables.

- **Roles:** org-level `owner|admin|member`; enforced by a FastAPI dependency `require_role(min_role)`.

- **Org context:** derive `org_id` from the organization user record. Reserve `X-Org-Id` for future multi-org support.

- **Share links:** public `GET /share/join?token=...` then `POST /share/join/resolve` **after auth** to create an Interview.