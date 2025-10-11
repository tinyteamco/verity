# Cross-Check: Over-Engineering & Constitution Compliance

**Date**: 2025-10-10
**Reviewer**: Claude Code
**Focus**: MVP-First Development (Constitution X) and avoiding over-engineering

---

## Constitution Compliance Review

### ✅ Constitution Principles Satisfied

1. **✅ BDD-First Development (I)**: quickstart.md shows BDD tests before implementation in every phase
2. **✅ Zero Warnings Policy (II)**: Using existing ruff + ty workflow
3. **✅ Multi-Tenancy Security (III)**: data-model.md includes detailed authorization checks, 403 denial tests
4. **✅ Transparent Tool Management (IV)**: Using mise + make
5. **✅ Outside-In Development (V)**: BDD-first workflow
6. **✅ Deployment-Complete Commits (VI)**: Existing GitHub Actions
7. **✅ Infrastructure as Code (VII)**: GCS bucket via Pulumi
8. **✅ Observability & Debugging (VIII)**: Structured logging mentioned
9. **✅ Stub Services Over Mocking (IX)**: No new external services

### 🔍 Constitution X: MVP-First Development - VIOLATIONS FOUND

**Principle**: "Build for current scale, not imagined future scale. Optimize when metrics show bottlenecks, not before."

**Deferred Until Needed**: Rate limiting, caching layers, advanced observability, performance optimization, data retention policies, advanced security beyond auth basics

---

## Over-Engineering Issues Identified

### 🚨 Issue 1: Cached Stats in ParticipantProfile (Premature Optimization)

**File**: data-model.md (lines ~300)
**Code**:
```python
class ParticipantProfile(Base):
    # Cached stats
    total_interviews: Mapped[int] = mapped_column(Integer, default=0)
    total_minutes_participated: Mapped[int] = mapped_column(Integer, default=0)
```

**Problem**: Denormalized caching for MVP scale (dozens of participants, handful of interviews each)

**Why Over-Engineered**:
- MVP scale: ~100 participants × ~5 interviews each = 500 total interviews
- Simple `COUNT(*)` query would be <1ms at this scale
- Adds complexity: must update counters on every interview completion
- Violates Constitution X: "Performance optimization (measure first, optimize second)"

**Constitution Guidance**: "Caching layers (add when latency measurements show need)"

**Fix**: Remove cached stats, use direct COUNT queries

**Impact**: Remove 2 fields, simplify interview completion logic

---

### 🚨 Issue 2: GCS Bucket Lifecycle Policy (Premature Data Retention)

**File**: research.md (line ~132), quickstart.md (line ~75)
**Code**:
```python
lifecycle_rules=[
    gcp.storage.BucketLifecycleRuleArgs(
        action=gcp.storage.BucketLifecycleRuleActionArgs(type="Delete"),
        condition=gcp.storage.BucketLifecycleRuleConditionArgs(age=90),
    ),
]
```

**Problem**: Automatic deletion after 90 days

**Why Over-Engineered**:
- MVP won't reach 90 days of data in initial deployment
- No requirement for data retention policy in spec
- Violates Constitution X: "Data retention policies (defer until storage costs become material)"
- Could accidentally delete valuable early data

**Fix**: Remove lifecycle policy, mark as "TBD based on usage patterns"

**Impact**: Remove 7 lines from Pulumi config, add comment about future retention

---

### 🚨 Issue 3: GCS Bucket Versioning (Premature Reliability Feature)

**File**: research.md (line ~136), quickstart.md (line ~82)
**Code**:
```python
versioning=gcp.storage.BucketVersioningArgs(
    enabled=True,
)
```

**Problem**: Versioning for accidental deletion recovery

**Why Over-Engineered**:
- MVP has no bulk delete operations
- Artifacts are write-once (pipecat uploads, never modified)
- Adds cost (storage for all versions)
- Violates Constitution X: "Advanced security (defer until needed)"

**Fix**: Remove versioning, rely on GCS's default durability (99.999999999%)

**Impact**: Remove 3 lines from Pulumi config

---

### 🚨 Issue 4: Interview.expires_at Field (Unused Complexity)

**File**: data-model.md (line ~106), quickstart.md (line ~287)
**Code**:
```python
expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**Problem**: Token expiration for single-use tokens

**Why Over-Engineered**:
- Tokens are already single-use (pending → completed invalidates token)
- Spec doesn't require expiration
- Research says "24 hours" but this is defensive programming for a problem that might not exist
- Adds code: must check expiration in GET /interview/{access_token}

**Counter-Argument**: Prevents token reuse if interview never completes (abandoned sessions)

**Decision**: Keep expires_at but simplify - set to 7 days (not 24 hours) and only check if interview is still pending

**Impact**: Clarify this is for abandoned sessions, not active interviews

---

### 🚨 Issue 5: Interview.completion_pending Status (Edge Case Handling)

**File**: data-model.md (line ~99)
**Code**:
```python
status: Mapped[str] = mapped_column(
    Enum("pending", "completed", "completion_pending", name="interview_status_enum"),
    ...
)
```

**Problem**: Three-state status for edge case between "pipecat uploading" and "callback received"

**Why Over-Engineered**:
- Spec only mentions pending/completed (two states)
- Adds complexity: more state transitions to handle
- Edge case: pipecat upload starts but callback fails
- MVP should fail fast: if callback doesn't arrive, interview stays pending

**Fix**: Remove "completion_pending", keep simple pending/completed

**Impact**: Simplify state machine, remove edge case handling

---

### ⚠️ Issue 6: Study.participant_identity_flow Enum (Premature Configuration)

**File**: data-model.md (line ~66)
**Code**:
```python
participant_identity_flow: Mapped[str] = mapped_column(
    Enum("anonymous", "claim_after", "allow_pre_signin", name="identity_flow_enum"),
    nullable=False,
    default="anonymous"
)
```

**Problem**: Three different participant identity flows configurable per study

**Spec Requirements**: FR-019 to FR-021 (optional participant sign-in)

**Why Potentially Over-Engineered**:
- Spec says "System MUST support optional participant sign-in"
- But does every study need this configured upfront?
- Could simplify: Start with one flow (anonymous with claim_after), add configuration later if researchers request it

**Counter-Argument**: FR-021 explicitly says "per-study basis"

**Decision**: Keep enum but simplify to 2 values initially:
- "anonymous" (default - no identity tracking)
- "optional_identity" (combines claim_after + allow_pre_signin)

Add "require_pre_signin" later if needed (YAGNI)

**Impact**: Reduce complexity, align with MVP scope

---

### ⚠️ Issue 7: Phase Prioritization (P2/P3 Features in Core Plan)

**File**: plan.md Implementation Roadmap

**Problem**: Phases 4, 6, 8 implement participant identity (P2-P3 user stories US7-US9)

**Why Potentially Over-Engineered**:
- P1 features (US1-US2): Reusable links + interview completion + artifacts
- P1 doesn't require participant identity at all
- Could ship MVP without Phases 4, 8 (participant claim + dashboard)

**MVP Core Flow**:
1. Researcher creates study with slug ✅
2. Participant accesses link with pid from Prolific ✅
3. Interview completes, artifacts uploaded ✅
4. Researcher views interviews by external_participant_id ✅

**Participant Identity Added Value**:
- Cross-platform tracking (same person, multiple platforms)
- Participant can view their own history
- But: Researcher can already track by external_participant_id from platform

**Decision**: Keep participant identity but clearly mark Phases 4, 8 as "P2 - Can defer to second iteration"

**Impact**: Allow team to ship P1 faster, add identity features after validating core flow

---

## Recommendations

### High Priority Fixes (Remove Over-Engineering)

1. **Remove cached stats from ParticipantProfile**
   - Delete `total_interviews`, `total_minutes_participated` fields
   - Use COUNT queries in participant dashboard endpoint
   - Update data-model.md, quickstart.md

2. **Remove GCS lifecycle policy**
   - Delete lifecycle_rules from Pulumi config
   - Add comment: "# Lifecycle: TBD based on usage (defer until storage costs material)"
   - Update research.md, quickstart.md

3. **Remove GCS versioning**
   - Delete versioning from Pulumi config
   - Rely on GCS default durability
   - Update research.md, quickstart.md

4. **Remove "completion_pending" status**
   - Simplify Interview.status to: pending, completed
   - Remove edge case handling in callback endpoint
   - Update data-model.md, contracts/api-endpoints.yaml

### Medium Priority Fixes (Simplify Configuration)

5. **Simplify participant_identity_flow enum**
   - Change to: "anonymous", "optional_identity" (combines claim + pre-signin)
   - Add "require_pre_signin" later if needed (YAGNI)
   - Update data-model.md, research.md

6. **Clarify Interview.expires_at purpose**
   - Change from 24 hours to 7 days (less aggressive)
   - Document: "For abandoned sessions only, not active interviews"
   - Update research.md, quickstart.md

### Low Priority (Documentation)

7. **Mark Participant Identity as P2**
   - Add note to plan.md: "Phases 4, 8 are P2 - can defer to second iteration"
   - Update Implementation Roadmap to show optional phases
   - Clarify MVP = Phases 1-3, 5-7 (core researcher workflow)

---

## Constitution Alignment After Fixes

### Before Fixes:
- ❌ Cached stats (premature optimization)
- ❌ Lifecycle policy (premature data retention)
- ❌ Versioning (advanced reliability)
- ⚠️ Complex status enum (edge case handling)

### After Fixes:
- ✅ No caching (direct queries, optimize if slow)
- ✅ No lifecycle (add when storage costs matter)
- ✅ No versioning (default durability sufficient)
- ✅ Simple status (pending/completed only)

**Constitution X Compliance**: ✅ PASS (after fixes)

---

## Impact Summary

**Lines Removed**: ~50 lines across data-model.md, research.md, quickstart.md, contracts/
**Complexity Reduced**:
- 2 database fields removed (cached stats)
- 1 enum value removed (completion_pending)
- 2 GCS features removed (lifecycle, versioning)
- 1 enum simplified (participant_identity_flow: 3→2 values)

**MVP Focus Improved**:
- Clear P1 vs P2 distinction
- Faster initial implementation (can skip participant identity for P1)
- Simpler Pulumi config (3 features removed)
- Simpler state machine (2 states instead of 3)

**Time Saved**: ~4 hours (removing Phases 4, 8 from P1 scope)

---

## Verification Checklist

After fixes:

- [ ] ParticipantProfile has no cached stats (use COUNT queries)
- [ ] GCS bucket has no lifecycle policy (comment: TBD based on usage)
- [ ] GCS bucket has no versioning (rely on default durability)
- [ ] Interview.status has only pending/completed (no completion_pending)
- [ ] Study.participant_identity_flow has 2 values (anonymous, optional_identity)
- [ ] Interview.expires_at documented as 7-day abandoned session cleanup
- [ ] Plan.md marks Phases 4, 8 as P2 (optional for MVP)
- [ ] All "premature optimization" removed per Constitution X

---

## Next Steps

1. Apply fixes to data-model.md (remove cached stats, simplify status enum)
2. Apply fixes to research.md (remove lifecycle/versioning, update expiration rationale)
3. Apply fixes to quickstart.md (update Pulumi code, simplify model examples)
4. Apply fixes to contracts/api-endpoints.yaml (remove completion_pending from status enum)
5. Apply fixes to plan.md (mark Phases 4, 8 as P2)
6. Commit with message: "refactor(spec): remove over-engineering per Constitution X (MVP-First)"
7. Verify all checklist items
