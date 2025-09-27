# Phase A — Foundations (Scaffold + Local Parity)

**Goal:** Boot a fully local, testable backend skeleton with MinIO storage, Firebase Auth emulator (two tenants), Postgres, and an in-process job runner. Zero managed services required.

---

## Scope (what’s in)
- FastAPI app with health, auth whoami, org bootstrap, studies & guides, share-link landing, interviews (create via share-link resolve), recording upload, transcript finalize (single segment), summary generation (async-shaped, fake-async runner).
- MinIO as object storage via a swappable `StoragePort`.
- Firebase Auth **emulator** with **two tenants**: `company`, `interviewee`.
- Postgres + Alembic migrations for MVP entities and `job` table.
- BDD test suite (pytest-bdd) covering happy paths and basic auth failures.
- Docker Compose for all services; `make test` spins & runs end-to-end.

## Out of scope (deferred)
Highlights, invites, legacy audio import, auto study summary triggers, Redis/Celery, streaming transcripts, billing/analytics, study-level ACLs.

---

## Deliverables checklist
- [ ] `openapi.yaml` (Company API MVP) – single source of truth.
- [ ] `docker-compose.yml` + `.env.example` – local stack.
- [ ] Alembic migrations (baseline + MVP entities + job).
- [ ] `storage/port.py` + `storage/minio_adapter.py` + `storage/memory_adapter.py`.
- [ ] Auth middleware (Firebase verify, tenant gate, org scoping).
- [ ] RBAC dependency (`require_role(min='member')`), roles: owner|admin|member.
- [ ] Share-link flow (create/rotate, landing, resolve -> create Interview).
- [ ] Upload endpoint (`POST /recordings:upload`) – streams to MinIO.
- [ ] Transcript finalize (`POST /interviews/{id}/transcript:finalize`) – one segment.
- [ ] Async job API (`POST :generate` -> 202+job_id, `GET /jobs/{id}`) with in-proc runner.
- [ ] BDD features + step skeletons (see `03_bdd_feature_scenarios.md`).

---

## Component breakdown & tasks
**1) Repo scaffold**: `api/`, `domain/`, `infra/` (db, storage, auth), `jobs/`, `tests/`; tools: ruff, black, mypy (opt), pytest, pytest-bdd; pre-commit.

**2) OpenAPI-first**: author `openapi.yaml` (see file 02); generate pydantic models; validate spec in CI.

**3) DB + migrations**: MVP IA entities + `job`; add `org_id` to tenant-scoped rows; RLS optional.

**4) Auth & tenancy**: Firebase emulator; assert `tenant in {company, interviewee}`; map tenant→table; derive `org_id` from `users.company_id`.

**5) Storage**: `StoragePort` + MinIO adapter; bucket bootstrap; key scheme.

**6) Share links**: token create/list; public landing; resolve->create interview.

**7) Recording upload**: multipart stream to MinIO; persist `AudioRecording`.

**8) Transcript finalize**: one full-span segment; persist JSONB segments.

**9) Summaries (fake-async)**: `job` row; in-proc runner claims/executes; writes summaries; status API.

**10) Tests**: BDD flows + unit tests for adapters, auth, jobs.

---

## Config (.env.example)

APP_ENV=local
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/uxr
FIREBASE_PROJECT_ID=uxr-local
FIREBASE_EMULATOR_HOST=firebase:9099
FIREBASE_ALLOWED_TENANTS=company,interviewee
JWT_SECRET=local-dev-secret-change-me
STORAGE_DRIVER=minio
MINIO_ENDPOINT=http://minio:9000
MINIO_REGION=us-east-1
MINIO_ACCESS_KEY=devminio
MINIO_SECRET_KEY=devminiosecret
MINIO_BUCKET_AUDIO=audio
MAX_UPLOAD_MB=200
JOBS_MODE=inproc
MAX_INPROC_JOBS=2

**Ports**: API 8000; Postgres 5432; MinIO 9000/9001; Firebase 9099.

---

## DoD (Phase A)
- `docker compose up` brings the stack; `/healthz` is 200.
- `make test` runs BDD + unit tests green.
- Upload + transcript + summary flows pass end-to-end.
- `/openapi.json` matches `openapi.yaml`.