# API Reference

This reference is scoped to the bundled structured-risk workflow. All helpers
should be used on synthetic or approved local tables only.

## `openmed.structured`

| Entry point | Purpose | Notes |
| --- | --- | --- |
| `scan_table` | Bounded role discovery for structured tables | Returns aggregate role evidence and candidate QI signals. |
| `profile_structured_table` | Higher-level structured table profiling | Useful when the task starts with a raw table rather than a release policy. |
| `anonymize_table` | Table anonymization orchestrator | Use for whole-table transformations when you do not need release-specific evidence. |
| `read_table` / `write_table` | Materialize and reread structured releases | Prefer these for round-tripping JSONL or Parquet artifacts. |
| `profile_quasi_identifiers` / `profile_qi` | Quasi-identifier risk profiling | Produces aggregate column-level risk evidence. |
| `apply_generalization_plan` | Reapply a chosen generalization plan | Useful when a task needs a deterministic replay of the selected plan. |
| `structured_privacy_fixture` / `make_synthetic_privacy_fixture` | Synthetic fixture generation | Keep the fixture synthetic and local. |

Role labels used during discovery include `ROLE_DIRECT_ID`, `ROLE_QUASI_ID`,
`ROLE_SENSITIVE`, `ROLE_SAFE`, `ROLE_INTERNAL_LINKAGE`, and `ROLE_FREE_TEXT`.

## `openmed.risk`

| Entry point | Purpose | Notes |
| --- | --- | --- |
| `AnonymityPolicy` | Explicit k/l/t release policy | Configure `quasi_identifiers`, `target_k`, `sensitive_attributes`, `privacy_unit`, `target_l`, `l_metric`, `target_t`, and suppression limits explicitly. |
| `assess_release` | Raw release assessment | Measures k-anonymity, l-diversity, t-closeness, and sample identity risk over the declared privacy unit. |
| `anonymize_release` | Release anonymization | Generalizes and suppresses complete privacy units, then re-validates the transformed result. |
| `validate_released_output` | Materialized-output validation | Use `preserve_scalar_types=False` for CSV/TSV round-trips. |
| `assess_population_risk` | Exact k-map / delta-presence analysis | Requires a reviewed sample table and a reviewed reference population table. |
| `analyze_k_anonymity` | Equivalence-class analysis | Returns the smallest class size and violating rows. |
| `propose_suppression` / `apply_suppression` | Minimal row suppression workflow | Helpful when the task wants the smallest row set that removes k violations. |
| `release_count` / `release_sum` / `release_mean` / `release_histogram` / `release_aggregate` | Differential-privacy aggregate release helpers | Keep the privacy budget explicit and review the utility report. |
| `utility_report` | DP utility summary | Useful for reporting the privacy/utility tradeoff. |
| `laplace_mechanism` / `gaussian_mechanism` | Noise mechanisms | Use only when the task explicitly calls for DP noise. |
| `membership_inference_self_test` / `run_membership_inference_self_test` | Table-level membership risk self-test | Treat as a risk check, not as a score to maximize. |
| `DifferentialPrivacy` / `PrivacyBudget` | DP budget management | Keep the configured budget in the artifact summary. |

Important `AnonymityPolicy` constraints:

- `target_k` must be at least 1.
- `target_l` must be at least 1.
- `target_t` must be between 0 and 1.
- `target_l > 1` or `target_t < 1` requires at least one sensitive attribute.
- A column cannot occupy conflicting roles in the same policy.
- `privacy_unit` may only overlap with `direct_identifiers`.

## `openmed.eval`

| Entry point | Purpose | Notes |
| --- | --- | --- |
| `evaluate_release_risk_evidence` | Integrity check for expert-review evidence | Use after building a structured release evidence bundle. |
| `evaluate_reidentification_risk_gate` / `evaluate_reid_risk_gate` | Re-identification risk gate | Accepts a structured risk report plus thresholds. |
| `evaluate_cross_document_linkage_gate` | Longitudinal linkage gate | Useful when release composition or cross-document linkage is in scope. |
| `build_leakage_dashboard` / `write_leakage_dashboard` | Leakage dashboard generation | Produces aggregate, shareable dashboard artifacts. |
| `compute_leakage_heatmap` | Leakage heatmap evidence | Useful for model or release leakage reports. |
| `run_benchmark` | Offline benchmark execution | Emits `BenchmarkReport` artifacts. |
| `BenchmarkReport` | Benchmark result container | Use for model/eval report handoff. |

## `openmed.compliance`

| Entry point | Purpose | Notes |
| --- | --- | --- |
| `build_release_expert_review_evidence` | Aggregate expert-review evidence | Used after validation to package a structured release summary. |
| `ExpertReviewEvidenceReport` | Parsed expert-review evidence | `from_json(...)` and `verify()` are the common follow-up steps. |
| `ReleaseAssumptions` | Release-context assumptions | Keep the release model, population scope, recipient model, and notes digest explicit. |
| `build_control_evidence_pack` / `generate_control_evidence_pack` | Control evidence output | Useful for audit and compliance handoff. |
| `build_part11_audit_trail` / `verify_part11_audit_trail` | Deterministic audit trail helpers | Helpful when the task asks for signed or replayable evidence. |
| `generate_safe_harbor_attestation` | Safe Harbor attestation helper | Use only when the task is actually about HIPAA Safe Harbor posture. |
| `create_expert_attestation` | Expert attestation envelope | Use as a separate signing step; OpenMed does not supply the conclusion. |

## Minimal structured release pattern

1. `scan_table(...)`
2. Build `AnonymityPolicy(...)`
3. `assess_release(rows, policy)`
4. `anonymize_release(rows, policy)`
5. `write_table(...)`
6. `read_table(...)`
7. `validate_released_output(...)`
8. `build_release_expert_review_evidence(...)`
9. `ExpertReviewEvidenceReport.from_json(...).verify()`

## CLI families

Use the family help commands to inspect concrete verbs and options:

- `openmed risk --help`
- `openmed audit --help`
- `openmed compliance --help`
- `openmed benchmark --help`
- `openmed eval --help`
- `openmed gates --help`
- `openmed calibrate --help`

Keep the output aggregate-only and synthetic when documenting or rehearsing a
workflow.
