---
name: comparison-and-quality
description: "Guides fg-data-profiling report comparison, privacy-safe reports,
  metadata, data dictionaries, quality outputs, and expectation-suite caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Comparison and Quality

Use this sub-skill when the user wants to compare datasets/reports, protect
sensitive data in a profile report, attach dataset metadata or data dictionaries,
inspect quality outputs, or discuss expectation-suite integration.

## Read first

- Read [references/comparison-workflows.md](references/comparison-workflows.md)
  for `compare([...])`, `profile_a.compare(profile_b)`, labels, constraints,
  and comparison output handling.
- Read [references/privacy-and-metadata.md](references/privacy-and-metadata.md)
  for `sensitive=True`, `samples=None`, custom synthetic samples, phone-number
  dtype risks, dataset metadata, column descriptions, and `type_schema`.
- Read [references/quality-outputs.md](references/quality-outputs.md) for
  `get_description()`, JSON output, alerts, and legacy Great Expectations notes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for
  comparison errors, privacy leaks, and expectation-suite dependency failures.
- Run [scripts/compare_reports_smoke.py](scripts/compare_reports_smoke.py) or
  [scripts/sensitive_report_smoke.py](scripts/sensitive_report_smoke.py) for
  safe no-network checks of comparison/privacy guidance.

## Comparison quick start

```python
from data_profiling import ProfileReport, compare

train_profile = ProfileReport(train_df, title="Train", minimal=True)
valid_profile = ProfileReport(valid_df, title="Validation", minimal=True)
comparison = compare([train_profile, valid_profile])
comparison.to_file("train-vs-validation.html")
```

`ProfileReport.compare(other)` is an alias for comparing two reports:

```python
comparison = train_profile.compare(valid_profile)
```

Reports use `config.title` as labels. Tune `report.precision` and
`html.style.primary_colors` when comparison tables are cramped.

## Privacy quick start

```python
profile = ProfileReport(
    df,
    title="Private profile",
    sensitive=True,
    samples=None,
    duplicates=None,
    minimal=True,
)
profile.to_file("private-profile.html")
```

For reports that need a sample section, replace real records with a synthetic
sample:

```python
profile = ProfileReport(
    df,
    sensitive=True,
    sample={"name": "Synthetic sample", "data": synthetic_df, "caption": "Synthetic rows only."},
)
```

This is redaction guidance, not enterprise PII detection. The open-source
package does not automatically manage organization-wide PII classifications.

## Metadata and quality quick start

```python
profile = ProfileReport(
    df,
    title="Dataset profile",
    dataset={"description": "5% reproducible sample", "creator": "Data team"},
    variables={"descriptions": {"amount": "Transaction amount"}},
    type_schema={"segment": "categorical"},
)
summary = profile.get_description()
json_text = profile.to_json()
```

## Boundaries

- Basic report creation belongs in
  [../profiling-workflows/SKILL.md](../profiling-workflows/SKILL.md).
- YAML/settings mechanics belong in
  [../configuration-and-output/SKILL.md](../configuration-and-output/SKILL.md).
- CLI command shapes belong in
  [../cli-and-automation/SKILL.md](../cli-and-automation/SKILL.md).
- Optional Great Expectations installation/version questions route to
  [../integrations-and-backends/SKILL.md](../integrations-and-backends/SKILL.md).
