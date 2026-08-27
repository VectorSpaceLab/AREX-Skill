---
name: mitigation-algorithms
description: "Choose and run AIF360 legacy bias mitigation algorithms with
  correct lifecycle stage, data contracts, optional extras, and metric checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AIF360 Mitigation Algorithms

Use this sub-skill when a task asks for legacy `aif360.algorithms` mitigation with AIF360 datasets: preprocessing, inprocessing, postprocessing, deterministic reranking, optional extras, fit/transform/predict patterns, and fairness-metric validation.

## Start here

1. Pick the lifecycle stage and class in [algorithm-selection.md](references/algorithm-selection.md).
2. Follow end-to-end usage patterns in [workflows.md](references/workflows.md).
3. Check optional dependency status and install hints in [optional-algorithms.md](references/optional-algorithms.md).
4. Diagnose install/import, optional-extra, data/API, score, and workflow failures in [troubleshooting.md](references/troubleshooting.md).
5. For a base-safe smoke, run [reweighing_smoke.py](scripts/reweighing_smoke.py) with `--help` before `--json`.

## Route neighboring tasks

- Dataset construction, `BinaryLabelDataset` fields, group dictionaries, raw dataset wrappers, and metrics: [datasets-and-metrics](../datasets-and-metrics/SKILL.md).
- `aif360.sklearn` estimators, pandas protected-attribute indexes, scorers, and sklearn pipelines: [sklearn-interface](../sklearn-interface/SKILL.md).
- MDSS/FACTS subgroup detection or metric text/JSON explainers: [detectors-and-explainers](../detectors-and-explainers/SKILL.md).

## Operating rules

- Select mitigation by where it acts: preprocessing modifies data before model training; inprocessing trains a mitigated model; postprocessing adjusts already-produced predictions; reranking reorders scored candidates.
- Keep true labels, predicted labels, `scores`, protected attributes, favorable/unfavorable labels, and privileged/unprivileged group values aligned across every dataset copy.
- Validate with AIF360 metrics before and after mitigation; a class name is not evidence that fairness improved.
- Optional extras were intentionally not installed in the construction environment. Mark optional workflows as optional/unverified until the user's runtime installs the named extra and passes a small smoke.
