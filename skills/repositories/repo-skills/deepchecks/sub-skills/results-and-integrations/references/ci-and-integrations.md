# CI and Integration Patterns

## Purpose

Read this when a user wants Deepchecks results to fail or pass automated workflows, while still preserving reports. These patterns assume another sub-skill already produced a `CheckResult` or `SuiteResult`.

## Conservative gating policy

For automated gates, prefer these defaults unless the user explicitly chooses softer behavior:

- Treat `WARN` as failing: `fail_if_warning=True`.
- Treat checks that could not run as failing at suite level: `fail_if_check_not_run=True`.
- Save HTML and/or JSON artifacts before any `assert`, `raise`, or `sys.exit(1)`.
- Use JSON gating only when the live result object is unavailable. Gating the live result object is more faithful than reconstructing a decision from a saved JSON structure.

## Pytest assertions

### Single-check pattern

```python
def test_feature_drift(train_dataset, test_dataset, tmp_path):
    from deepchecks.tabular.checks import FeatureDrift

    check = FeatureDrift(columns=["age", "income"])
    check.add_condition_drift_score_not_greater_than(
        max_allowed_psi_score=0.2,
        max_allowed_earth_movers_score=0.1,
    )

    result = check.run(train_dataset, test_dataset)
    html_path = result.save_as_html(str(tmp_path / "feature_drift.html"), connected=False)

    assert result.passed_conditions(fail_if_warning=True), f"Deepchecks report: {html_path}"
```

### Suite pattern

```python
def test_deepchecks_suite(train_dataset, test_dataset, model, tmp_path):
    from deepchecks.tabular.suites import model_evaluation

    suite_result = model_evaluation().run(train_dataset=train_dataset, test_dataset=test_dataset, model=model)
    html_path = suite_result.save_as_html(str(tmp_path / "model_evaluation.html"), connected=False)

    not_passed = [r.get_header() for r in suite_result.get_not_passed_checks(fail_if_warning=True)]
    not_ran = [r.get_header() for r in suite_result.get_not_ran_checks()]

    assert suite_result.passed(fail_if_warning=True, fail_if_check_not_run=True), (
        f"Deepchecks failed; report={html_path}; not_passed={not_passed}; not_ran={not_ran}"
    )
```

Notes:

- Use the modality sub-skills to construct `train_dataset`, `test_dataset`, `TextData`, or `VisionData` correctly.
- Keep report filenames deterministic enough for artifact upload, but capture the return value because Deepchecks may choose a non-conflicting filename if the target already exists.
- If a suite intentionally includes advisory `WARN` conditions, choose `fail_if_warning=False` only after the user confirms that warnings should not fail CI.

## GitHub Actions artifact and gate pattern

A distilled workflow shape:

```yaml
name: Deepchecks validation

on:
  pull_request:
  push:
    branches: [main]

jobs:
  deepchecks:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - name: Install project and Deepchecks
        run: |
          python -m pip install --upgrade pip
          python -m pip install deepchecks
          python -m pip install -r requirements.txt
      - name: Run validation tests
        run: pytest your_deepchecks_tests/ -q
      - name: Upload Deepchecks reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: deepchecks-reports
          path: |
            deepchecks-reports/*.html
            deepchecks-results/*.json
```

Use `if: always()` for the upload step so reports remain available after a failed validation step. Keep credentials and production deployment steps separate from Deepchecks validation unless the user explicitly requests a deployment workflow.

## Gating from saved JSON

When a pipeline produces a Deepchecks JSON artifact and a later step must decide pass/fail without rerunning checks:

```bash
python sub-skills/results-and-integrations/scripts/deepchecks_ci_result_gate.py deepchecks_result.json
```

The bundled [CI gate script](../scripts/deepchecks_ci_result_gate.py):

- Reads one JSON file created by `CheckResult.to_json(...)` or `SuiteResult.to_json(...)`.
- Fails non-zero for malformed JSON, unsupported result structure, failing/error conditions, warning conditions by default, not-run checks by default, or a result with no conditions unless explicitly allowed.
- Does not import Deepchecks, call the network, read credentials, upload artifacts, or write files by default.
- Is a structural fallback. If the live `SuiteResult` object is available, prefer `suite_result.passed(...)`.

## Preserve artifacts while failing CI

A robust local validation script should write both HTML and JSON before it exits non-zero:

```python
import sys
from pathlib import Path

suite_result = suite.run(train_dataset=train, test_dataset=test, model=model)
html_path = suite_result.save_as_html("deepchecks_report.html", connected=False)
Path("deepchecks_result.json").write_text(suite_result.to_json(with_display=False), encoding="utf-8")

if not suite_result.passed(fail_if_warning=True, fail_if_check_not_run=True):
    print(f"Deepchecks failed; report saved to {html_path}", file=sys.stderr)
    sys.exit(1)
```

## Airflow and S3 adapter pattern

Use Airflow only as an orchestrator around ordinary Deepchecks code:

1. Load or materialize the input data in an Airflow task.
2. Build Deepchecks data objects using the appropriate modality sub-skill.
3. Run `data_integrity()`, `train_test_validation()`, or `model_evaluation()` as appropriate.
4. Save HTML to task-local storage before returning or raising.
5. Upload HTML/JSON to object storage only with an explicitly configured connection, bucket, and key.
6. Return `suite_result.passed(...)` from a short-circuit task when downstream steps should be skipped on validation failure, or raise an Airflow exception when the DAG run itself should fail.

Caveats:

- Airflow providers, object-storage clients, connection IDs, buckets, and credentials are optional external dependencies. Do not embed secrets in the DAG.
- Object-storage uploads are side effects. Do not run or bundle an S3 DAG as a default script.
- XCom should carry small metadata or paths, not full model objects or large result payloads.
- Use deterministic report names or run IDs so retries do not hide the artifact that caused the failure.

## H2O adapter signals

Treat H2O integration as an adapter pattern rather than as a Deepchecks-native model type:

- Convert `H2OFrame` data to a tabular structure that `deepchecks.tabular.Dataset` can wrap, or create a small adapter that exposes predictions in a pandas/numpy shape expected by Deepchecks.
- If the H2O model does not expose sklearn-like `predict` / probability behavior, precompute predictions/probabilities and route to the tabular-validation guidance for supplied prediction workflows.
- H2O can start local or remote services and may require cluster lifecycle management. Do not run H2O initialization as part of a generic CI result-gating script.
- Once a Deepchecks result exists, use the same `save_as_html`, `to_json`, and `passed` patterns as any other tabular workflow.

## Hugging Face adapter signals

Treat Hugging Face integrations as model/data adapters feeding Deepchecks, not as result-export mechanisms:

- NLP: use `TextData` plus labels, metadata, properties, embeddings, and supplied predictions/probabilities when possible; avoid model downloads in CI by using precomputed outputs.
- Vision: adapt a processor/dataloader/model output into the `VisionData` batch format and task-specific prediction structures before running checks.
- Model weights, tokenizers, image datasets, and GPU execution can trigger network or hardware side effects. Keep those steps outside the bundled result gate and make them explicit in project pipelines.
- After checks run, save/gate the resulting `CheckResult` or `SuiteResult` with this sub-skill.

## Optional lower-level CI/report serializers

Use these only when the user's CI system explicitly wants them; they are not required for the default pytest/GitHub Actions gate above.

```python
# JUnit XML for CI systems that ingest test reports.
from deepchecks.core.serialization.suite_result.junit import SuiteResultSerializer as JunitSerializer
xml_text = JunitSerializer(suite_result).serialize(failure_tag="failure")

# CML-style markdown summary plus optional attached HTML report.
suite_result.save_as_cml_markdown(
    file="deepchecks_report.md",
    platform="github",
    attach_html_report=True,
)
```

Caveats: JUnit serialization is a lower-level serializer object, not `suite_result.to_junit()`. CML markdown generation is local, but posting comments or publishing artifacts through CML is an external CI side effect and should be configured in the user's pipeline.

## Source example decisions

- Airflow and S3 examples are reference-only because they require Airflow runtime setup, object-storage providers, credentials, buckets, and write side effects.
- H2O examples are reference-only because they are intended as integration inspiration and may require an H2O runtime or notebook environment.
- Hugging Face examples are reference-only because they can download model weights and datasets and may require a GPU or large local assets.
- The bundled result gate script is the only runnable helper in this sub-skill because it is local, deterministic, and safe by default.
