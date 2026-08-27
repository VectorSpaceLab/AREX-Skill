---
name: aif360
description: "Use IBM AI Fairness 360 for tabular fairness datasets, metrics,
  bias mitigation algorithms, sklearn-compatible workflows, subgroup detectors,
  and explainers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AIF360 Repo Skill

Use this skill when a task involves the AI Fairness 360 (`aif360`) Python
package: fairness datasets, group-fairness metrics, bias-mitigation algorithms,
the preferred `aif360.sklearn` API, MDSS/FACTS subgroup detectors, or metric
explainers.

## Install and smoke-check first

Base package install:

```bash
pip install aif360
python -c "import aif360; print(aif360.__version__)"
```

For local package development, use an editable install in an isolated Python
environment. For optional algorithms, install the smallest named extra that
matches the requested workflow rather than `aif360[all]` by default; read
[install-data-and-optional-deps.md](references/install-data-and-optional-deps.md).

Run the bundled base smoke when importability or optional-warning noise is
unclear:

```bash
python scripts/check_aif360_env.py --json
```

The smoke uses only synthetic in-memory data and does not download benchmark
datasets or require optional extras.

## Route by task

| Task signal | Read |
| --- | --- |
| Legacy `BinaryLabelDataset`, `StructuredDataset`, standard dataset wrappers, `BinaryLabelDatasetMetric`, `ClassificationMetric`, raw-data availability, or protected group dictionaries | [datasets-and-metrics](sub-skills/datasets-and-metrics/SKILL.md) |
| Legacy `aif360.algorithms` preprocessing, inprocessing, postprocessing, deterministic reranking, optional mitigation extras, or before/after metric validation | [mitigation-algorithms](sub-skills/mitigation-algorithms/SKILL.md) |
| Preferred pandas/sklearn API, `aif360.sklearn.datasets.fetch_*`, protected attributes in pandas indexes, sklearn metrics/scorers, sklearn estimators, or `PostProcessingMeta` | [sklearn-interface](sub-skills/sklearn-interface/SKILL.md) |
| MDSS subgroup bias scan, FACTS recourse subgroup reports, `MetricTextExplainer`, or `MetricJSONExplainer` | [detectors-and-explainers](sub-skills/detectors-and-explainers/SKILL.md) |
| Install/import failures, raw dataset files, optional extras, warnings, Python versions, R wrapper, or MLOps sample boundaries | Root references below |

## Core decision points

- **Legacy vs sklearn API**: choose legacy APIs for `BinaryLabelDataset` and
  legacy algorithms; choose `aif360.sklearn` for pandas/sklearn pipelines and
  future-facing DataFrame workflows.
- **Data availability**: AIF360 documents common benchmark datasets, but most
  raw files are not bundled. Do not download data unless the user approves data
  acquisition and terms.
- **Optional extras**: many algorithms are public but extra-gated. Missing
  TensorFlow, fairlearn, torch, cvxpy, BlackBoxAuditing, POT, FACTS, or R/rpy2
  packages are not base-install failures unless the selected workflow needs
  them.
- **Fairness semantics**: always make `favorable_label`, `pos_label`,
  privileged group, unprivileged group, protected attributes, and row alignment
  explicit before interpreting a metric or detector result.
- **Verification status**: this skill verified base CPU package imports and
  synthetic dataset/metric workflows. Optional-extra workflows are documented
  but must be installed and smoke-tested in the user's runtime before claiming
  execution support.

## Root references and scripts

- [repo-provenance.md](references/repo-provenance.md): source snapshot and
  refresh baseline for this generated skill.
- [repo-routing-metadata.json](references/repo-routing-metadata.json): structured
  metadata for repo-skills-router import.
- [install-data-and-optional-deps.md](references/install-data-and-optional-deps.md):
  package install variants, extras, standard dataset data constraints, and
  construction verification status.
- [troubleshooting.md](references/troubleshooting.md): cross-cutting import,
  optional dependency, data, API-family, and workflow recovery guidance.
- [r-and-mlops-notes.md](references/r-and-mlops-notes.md): boundaries for the R
  package wrapper and platform integration samples.
- [check_aif360_env.py](scripts/check_aif360_env.py): safe base environment
  diagnostic helper.

## Quick operating checklist

1. Identify whether the user is using legacy datasets or `aif360.sklearn`.
2. Confirm data source and raw-data/network permissions.
3. Confirm protected attributes, privileged/unprivileged groups, and favorable
   labels.
4. Install only the base package plus selected extras needed by the workflow.
5. Run a bundled synthetic smoke before running real data or optional training.
6. Use metrics or detectors to diagnose bias, then route to mitigation only if
   the user asks to change data/model/predictions.
7. If the current package commit/version differs from [repo-provenance.md](references/repo-provenance.md), refresh this skill before relying on exact API claims.
