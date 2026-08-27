---
name: structured-risk-evaluation
description: "Structured tabular de-identification, release-risk evaluation, and
  compliance evidence."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Structured Risk Evaluation

Use this sub-skill for synthetic or approved tabular release workflows that need
quasi-identifier discovery, k-anonymity, l-diversity, t-closeness, differential
privacy aggregates, membership risk, anonymized output validation, and
compliance evidence.

## Route elsewhere when the task is about

- Free-text PHI or PII redaction → deidentification-privacy.
- Clinical entity extraction or grounding → clinical-extraction-grounding.
- Service deployment, transport, or adapter wiring → interoperability-serving.

## Core surfaces

- `openmed.structured`
- `openmed.risk`
- `openmed.eval`
- `openmed.compliance`
- CLI families: `risk`, `audit`, `compliance`, `benchmark`, `eval`, `gates`, `calibrate`

## Safe workflow

1. Discover candidate direct identifiers, quasi-identifiers, sensitive columns,
   and the privacy unit with `scan_table` or `profile_structured_table`.
2. Review the policy explicitly; do not infer threshold values.
3. Assess the raw table with `assess_release`, `analyze_k_anonymity`,
   `assess_population_risk`, or the DP and membership helpers that match the
   task.
4. Anonymize with `anonymize_release` or `anonymize_table`.
5. Re-read the materialized release and validate with
   `validate_released_output`.
6. Package aggregate-only audit/compliance evidence and, when needed, feed it
   into release gates and dashboards.
7. Keep all examples synthetic. Never depend on DUA-restricted rows, raw PHI,
   or deployment-time services.

## Bundled references

- `references/risk-eval-workflows.md`
- `references/api-reference.md`
- `references/troubleshooting.md`

## Bundled helper script

- `scripts/structured_release_check.py`

## Output expectations

- Aggregate JSON summaries only.
- Evidence files may include Markdown and JSON, but never raw cell values.
- Release artifacts should be materialized locally, reread, and validated before
  review or gating.
