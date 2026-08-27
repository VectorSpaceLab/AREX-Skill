---
name: extension-development
description: "Build and debug sktime-compatible estimators, extension templates,
  tags, soft dependencies, and focused estimator checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Extension Development

Use this sub-skill when implementing, debugging, or maintaining an `sktime`-compatible estimator or extension package.

## Route here

- Choose an extension template for a forecaster, transformer, classifier, regressor, clusterer, detector, aligner, splitter, metric, or parameter fitter.
- Implement private hooks such as `_fit`, `_predict`, `_transform`, or `_split`.
- Set tags for mtypes, capabilities, soft dependencies, maintainers, and tests.
- Debug `check_estimator`, `get_test_params`, or focused pytest failures.
- Isolate soft dependencies and decide when `tests:vm` is required.

## Route away

User-level forecasting, panel learning, data conversion, or evaluation workflows belong to their respective sub-skills. Release automation and CI-specific host setup are outside this operating skill unless explicitly requested.

## References and helper

- [Extension templates](references/extension-templates.md) for scitype-to-template mapping and private method contracts.
- [Testing and maintenance](references/testing-and-maintenance.md) for `check_estimator`, test scenarios, soft dependency policy, and focused checks.
- [Troubleshooting](references/troubleshooting.md) for common estimator failures.
- Use [scripts/scaffold_estimator.py](scripts/scaffold_estimator.py) to list template mappings or generate a tiny stub, and [scripts/check_estimator_smoke.py](scripts/check_estimator_smoke.py) for focused conformance diagnostics.
