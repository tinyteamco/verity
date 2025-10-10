# Fixes to Apply - Over-Engineering Removal

## File: data-model.md

### Fix 1: Remove cached stats from ParticipantProfile (lines 253-254, 260-261, 263, 280-281, 291-292)
- Remove `total_interviews` field
- Remove `total_minutes_participated` field
- Update validation rules
- Update state transitions note
- Update example
- Update SQL schema

### Fix 2: Remove "completion_pending" from Interview status (lines 99, 114, 122, 124-125, 165)
- Change enum to: pending, completed (remove completion_pending)
- Update validation rules
- Update state transitions
- Update SQL CHECK constraint

### Fix 3: Update Interview.expires_at documentation (lines 102, 147, 316)
- Change from "24 hours" to "7 days"
- Add note: "For abandoned sessions only, not active interviews"

## File: research.md

### Fix 4: Remove GCS lifecycle policy (section 3.1)
- Remove lifecycle_rules from Pulumi example
- Add comment: "# Lifecycle: TBD based on usage (defer until storage costs material)"

### Fix 5: Remove GCS versioning (section 3.1)
- Remove versioning from Pulumi example

### Fix 6: Update expires_at to 7 days (section 1.3)
- Change from "24 hours (86400 seconds)" to "7 days (604800 seconds)"
- Update rationale

## File: quickstart.md

### Fix 7: Update Pulumi code example (Phase 1)
- Remove lifecycle_rules
- Remove versioning
- Add comment about TBD lifecycle

### Fix 8: Update Interview model example (Phase 2)
- Remove completion_pending from status enum
- Change expires_at calculation to 7 days

### Fix 9: Update ParticipantProfile model (Phase 2)
- Remove cached stats fields
- Add comment about COUNT queries

## File: contracts/api-endpoints.yaml

### Fix 10: Remove completion_pending from status enum
- Interview status: pending, completed (only)

## File: plan.md

### Fix 11: Mark Phases 4, 8 as P2 (Implementation Roadmap)
- Add note to Phase 4: "(P2 - Can defer to second iteration after P1 validation)"
- Add note to Phase 8: "(P2 - Can defer to second iteration after P1 validation)"
- Update MVP definition
