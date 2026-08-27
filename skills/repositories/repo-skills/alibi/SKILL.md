---
name: alibi
description: "Routes Alibi users to the right explanation, confidence,
  prototype, or optional-backend workflow and points them to the bundled helpers
  needed to run it."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Alibi

Alibi is a Python library for model explanation, confidence scoring, prototype selection, and explanation persistence.

## When to use this skill

Use this skill when a user asks how to:

- install Alibi or choose extras
- inspect public Alibi APIs
- run a small reproducible Alibi workflow
- decide which explanation family fits a task
- diagnose `MissingDependency`, backend, or predictor-shape issues

## First reads

- `references/workflows.md` for the route map
- `references/optional-dependencies.md` for extras and `MissingDependency` placeholders
- `references/troubleshooting.md` for import, backend, and workflow failures
- `references/repo-provenance.md` when checking staleness or before refresh work
- `references/api-reference.md` for verified constructor signatures and return shapes

## Minimal install and import

- `python -m pip install alibi`
- From a checkout: `python -m pip install -e .`
- Minimal import check: `python -c "import alibi; print(alibi.__version__)"`
- If the import trips over a spaCy / `click` issue, repair the base environment before assuming the package is broken.

## Route map

### `sub-skills/global-tabular-explanations/`
Use for ALE, partial dependence, PD variance, permutation importance, and other global tabular feature-effect workflows.

### `sub-skills/anchors-local-explanations/`
Use for AnchorTabular, AnchorText, and AnchorImage workflows, including text sampling and image segmentation guidance.

### `sub-skills/attribution-and-shap/`
Use for KernelShap, TreeShap, and IntegratedGradients, plus optional SHAP / TensorFlow backend selection.

### `sub-skills/counterfactuals-and-similarity/`
Use for Counterfactual, CEM, CounterfactualProto, CounterfactualRL, and GradientSimilarity workflows.

### `sub-skills/confidence-prototypes-utilities/`
Use for TrustScore, LinearityMeasure, ProtoSelect, and save/load round-trips.

## Helper scripts

- `scripts/core_smoke.py` runs a tiny CPU smoke across the base tabular workflows.
- `scripts/check_optional_backends.py` reports which optional exports are placeholders and which extra enables them.

## What not to do

- Do not treat a `MissingDependency` placeholder as a verified runtime path.
- Do not send users to the source checkout for docs, examples, or notebooks.
- Do not assume optional backends are installed until the helper says so.
