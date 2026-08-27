# Troubleshooting

## Optional table extras are missing

**Symptom:** `scan_table`, `read_table`, or `write_table` fails because a table
backend is unavailable.

**Fix:** Use a supported local file format first (`JSONL`, `CSV`, `TSV`, or
`Parquet`), or install the optional table extras that the task requires. Keep
all fallback data synthetic and local.

## The quasi-identifier policy is invalid

**Symptom:** `AnonymityPolicy` raises a role overlap or threshold error.

**Fix:** Check these rules:

- `target_k >= 1`
- `target_l >= 1`
- `0 <= target_t <= 1`
- `target_l > 1` requires at least one sensitive attribute
- `target_t < 1` requires at least one sensitive attribute
- A column cannot be both a quasi-identifier and a sensitive/direct/non-
  sensitive/excluded attribute in the same policy
- `privacy_unit` may only also appear in `direct_identifiers`

If the release needs both direct-linkage and privacy-unit semantics, keep the
privacy unit explicit and review the policy roles again.

## The raw table has a too-small equivalence class

**Symptom:** `assessment.achieved_k < target_k` or `k_violating_class_count > 0`.

**Fix:** Generalize, suppress, or narrow the release scope. If the task allows
remediation, rerun the anonymization and validate the materialized output.
If the task does not allow remediation, keep the failure explicit in the
summary and do not downgrade the policy silently.

## DUA-restricted or licensed data appears in the path

**Symptom:** A dataset is not synthetic, not user-supplied, or has restricted
terms attached to it.

**Fix:** Stop and replace it with a synthetic fixture or a user-provided local
copy that is allowed for the task. Do not bundle the restricted table into the
skill tree, the example output, or the release evidence.

## Signed evidence keys are missing

**Symptom:** Evidence verification or attestation signing cannot proceed.

**Fix:** The runtime can build aggregate evidence, but key custody belongs
outside the skill tree. Provide the signing material through the caller's local
secret-management path, then rerun the evidence verification step.

## Release artifacts are hard to inspect

**Symptom:** The output exists only in memory, or the materialized release was
never reread.

**Fix:** Write separate artifacts for discovery, assessment, release,
validation, and evidence. Reopen the release bytes with `read_table(...)`, then
run `validate_released_output(...)` on the reread rows. For CSV/TSV, set
`preserve_scalar_types=False` when the format cannot preserve types faithfully.

## Evidence verification fails

**Symptom:** `ExpertReviewEvidenceReport.from_json(...).verify()` returns false
or raises.

**Fix:** Check for truncated JSON, mismatched digests, unsupported schema
versions, or a release artifact that changed after evidence generation. Rerun
from the same materialized release and regenerate the evidence bundle.

## Differential-privacy budgets are exhausted

**Symptom:** A DP helper raises a budget error.

**Fix:** Treat the budget as consumed, not as a transient glitch. Recompute the
requested aggregate with a fresh policy, a different budget, or a smaller set of
statistics.
