# Risk and Evaluation Workflows

This sub-skill focuses on table-shaped release workflows that stay local,
synthetic, and aggregate-only. Treat the steps below as the default ordering
unless a task explicitly asks for a narrower slice.

## 1) Discover roles before setting a policy

Start with a bounded scan so the review can separate direct identifiers,
quasi-identifiers, sensitive attributes, and the privacy unit.

```python
from openmed.structured import scan_table

roles = scan_table(
    "synthetic-cohort.jsonl",
    privacy_unit="patient_id",
    quasi_identifier_columns=("age", "zip", "visit_date"),
    sensitive_columns=("diagnosis",),
    role_overrides={
        "patient_id": "direct-id",
        "full_name": "direct-id",
        "encounter_id": ("direct-id", "internal-linkage"),
    },
)
```

Review the returned aggregates and then set the policy explicitly. Do not let
heuristics choose the final thresholds.

## 2) Assess the raw release

Use `assess_release` when the question is whether the unmodified table already
meets the declared k/l/t criteria.

```python
from openmed.risk import AnonymityPolicy, assess_release

policy = AnonymityPolicy(
    quasi_identifiers=("age", "zip", "visit_date"),
    sensitive_attributes=("diagnosis",),
    direct_identifiers=("full_name", "encounter_id"),
    privacy_unit="patient_id",
    target_k=2,
    target_l=2,
    l_metric="distinct",
    target_t=0.0,
)
assessment = assess_release(rows, policy)
```

Read the aggregate report, especially:

- `achieved_k`
- `k_violating_class_count`
- `l_violating_class_count`
- `t_violating_class_count`
- `warnings`

If the raw table fails, keep the failure explicit. Do not silently downgrade the
policy.

## 3) Anonymize, reread, and validate

Use this sequence when the release may be generalized or suppressed.

```python
from openmed.risk import anonymize_release, validate_released_output
from openmed.structured import read_table, write_table

result = anonymize_release(rows, policy)
write_table(release_path, result.records)
reread_rows = read_table(release_path)
validation = validate_released_output(reread_rows, result)
```

A good summary should report:

- whether the raw table contained a too-small equivalence class
- whether the transformed release meets the same policy
- whether the reread artifact passed validation
- which artifact files were written

## 4) Assess reference-population risk when a reviewer supplies the attack table

Use `assess_population_risk` only when the caller has a reviewed reference
population and the task is about exact k-map / delta-presence evidence.

```python
from openmed.risk import assess_population_risk

population_risk = assess_population_risk(
    sample_rows,
    reference_rows,
    ("age_band", "region"),
    sample_privacy_unit="sample_id",
    population_privacy_unit="population_id",
    target_k_map=2,
    max_delta_presence=0.5,
)
```

This workflow is exact over the supplied rows. It does not fetch or infer an
external population.

## 5) Use differential privacy helpers for aggregate releases

For aggregate statistics, prefer the DP helpers rather than exposing raw class
membership.

Typical entry points:

- `openmed.risk.release_count`
- `openmed.risk.release_sum`
- `openmed.risk.release_mean`
- `openmed.risk.release_histogram`
- `openmed.risk.release_aggregate`
- `openmed.risk.utility_report`
- `openmed.risk.laplace_mechanism`
- `openmed.risk.gaussian_mechanism`

Keep the budget explicit and include the budget object in the summary.

## 6) Use membership and leakage checks as gates, not as scores

Risk and leakage checks are decision aids. They are not a legal conclusion and
not a substitute for expert review.

Useful families:

- `openmed.risk.membership_inference_self_test`
- `openmed.risk.run_membership_inference_self_test`
- `openmed.eval.evaluate_reidentification_risk_gate`
- `openmed.eval.evaluate_reid_risk_gate`
- `openmed.eval.evaluate_release_risk_evidence`
- `openmed.eval.build_leakage_dashboard`
- `openmed.eval.write_leakage_dashboard`
- `openmed.eval.compute_leakage_heatmap`

Use these on synthetic or approved evaluation artifacts only. Gate failures
should report aggregate reasons without echoing raw values.

## 7) Package compliance evidence after the release check

A typical release bundle contains:

- discovery manifest
- pre-release assessment
- anonymized output
- reread validation report
- expert-review evidence JSON and Markdown
- optional audit trail or control evidence pack

Keep evidence deterministic and reproducible. When a task needs provenance or
attestation, package it separately from the data artifact.
