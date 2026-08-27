---
name: results-and-integrations
description: "Use for Deepchecks result export, JSON recovery, CI gating, pytest
  assertions, and safe integration-adapter patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Results and Integrations

Use this sub-skill when a task already has a Deepchecks `CheckResult` or `SuiteResult`, or when the user asks how to preserve, display, serialize, reconstruct, or gate Deepchecks results in tests and pipelines.

## Route by task

- Need exact result APIs, signatures, JSON shape, HTML output options, or display methods: read [references/api-reference.md](references/api-reference.md).
- Need pytest assertions, CI gates, GitHub Actions artifact upload, or safe Airflow/S3/H2O/Hugging Face adapter patterns: read [references/ci-and-integrations.md](references/ci-and-integrations.md).
- Need to gate a saved Deepchecks result JSON without rerunning the suite: use [scripts/deepchecks_ci_result_gate.py](scripts/deepchecks_ci_result_gate.py) and then check [references/troubleshooting.md](references/troubleshooting.md) for exit codes and malformed JSON guidance.
- Need help with blank widgets, offline HTML, JSON reconstruction, missing optional integration packages, warnings, not-run checks, or CI failures: read [references/troubleshooting.md](references/troubleshooting.md).

## Boundaries

This sub-skill owns result handling and integration control flow only. Route construction of Deepchecks inputs and suites elsewhere:

- Tabular `Dataset`, tabular checks, and tabular suites: [../tabular-validation/SKILL.md](../tabular-validation/SKILL.md).
- NLP `TextData`, text properties, embeddings, labels, and NLP suites: [../nlp-validation/SKILL.md](../nlp-validation/SKILL.md).
- Vision `VisionData`, batch loaders, Hugging Face model-output adapters, and vision suites: [../vision-validation/SKILL.md](../vision-validation/SKILL.md).
- Package installation, global import failures, optional extra selection, and latest-version-check behavior: the root Deepchecks troubleshooting reference.

Do not bundle or run Airflow/S3/H2O/Hugging Face examples as scripts: those patterns can require credentials, network access, external services, model downloads, or large data. Distill their control flow, make side effects explicit, and prefer precomputed predictions or local artifacts in CI.

## Minimal result workflow

1. Run the appropriate Deepchecks suite/check using the modality-specific sub-skill.
2. Save artifacts before failing the pipeline:
   - `result.save_as_html("deepchecks_report.html", connected=False)` for an HTML report.
   - `result.to_json(with_display=False)` for a smaller CI gate JSON, or `with_display=True` when later display reconstruction matters.
3. Gate with the native API when the live result object is available:
   - `assert check_result.passed_conditions(fail_if_warning=True)`.
   - `assert suite_result.passed(fail_if_warning=True, fail_if_check_not_run=True)` for a conservative CI gate.
4. Gate from a saved JSON only when rerunning the suite is impractical; use the bundled script and document that structural JSON gating is less complete than gating the original result object.
