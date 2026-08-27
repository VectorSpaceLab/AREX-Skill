---
name: tabpfn
description: "Routes TabPFN tabular foundation-model workflows across
  prediction, preprocessing, batched inference, tuning, and model-management
  tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TabPFN

TabPFN is the sklearn-style tabular foundation-model package in this repository.
Use this skill as the top-level router when the task mentions `tabpfn`,
`TabPFNClassifier`, `TabPFNRegressor`, model downloads, preprocessing rules,
batched scoring, tuning, or fitted-model persistence.

## Start here

- Read `references/package-overview.md` for the package scope and the main public entry points.
- Read `references/installation.md` for the safe install path and first-use model access flow.
- Read `references/model-overview.md` for model versions, cache resolution, and version selection.
- Run `scripts/check_tabpfn_environment.py --help` for the safe environment helper.

Install:

```bash
pip install tabpfn
python -c "import tabpfn; print(tabpfn.__version__)"
```

If you need plotting or experiment logging, install the matching extra for the
workflow you are using. Keep this skill self-contained: do not depend on the
original repository checkout at runtime.

## Route by task

| User task | Read |
| --- | --- |
| Choose between classifier and regressor, interpret `predict`, `predict_proba`, `predict_logits`, `predict_raw_logits`, or fit a single tabular dataset | `sub-skills/tabular-prediction/SKILL.md` |
| Diagnose DataFrame, categorical, text, NaN, infinity, sample-limit, or `InferenceConfig` / `PreprocessorConfig` issues | `sub-skills/preprocessing-config/SKILL.md` |
| Score many train/test datasets in one call, compare batched vs non-batched prediction, or tune cache / memory settings | `sub-skills/batched-performance/SKILL.md` |
| Calibrate, tune, prompt-tune, differentiate through inputs, or fine-tune the model | `sub-skills/tuning-and-advanced/SKILL.md` |
| Download, cache, authenticate, save, load, convert, or visualize models and checkpoints | `sub-skills/model-management/SKILL.md` |

## Fast routing rules

- If the task is about one dataset and ordinary sklearn semantics, start with `tabular-prediction`.
- If the task is about input cleaning, data validation, feature modality detection, or config fields, start with `preprocessing-config`.
- If the task mentions CV folds, multiple datasets, `predict_proba_batched`, `predict_batched`, `fit_with_cache`, or chunking, start with `batched-performance`.
- If the task mentions `eval_metric`, `tuning_config`, `differentiable_input`, `FinetunedTabPFN*`, or prompt tuning, start with `tuning-and-advanced`.
- If the task mentions checkpoints, cache/auth, `TABPFN_TOKEN`, `TABPFN_MODEL_CACHE_DIR`, `.tabpfn_fit`, `safetensors`, or saved models, start with `model-management`.

## Common expectations

- `TabPFNClassifier` and `TabPFNRegressor` are sklearn-style estimators.
- The default model version is `v3`; older versions are available through `ModelVersion`.
- TabPFN can work with DataFrames, categoricals, NaNs, and selected text-like columns, but free text is usually a bad feature choice.
- Batched inference has stricter shape and class-set constraints than ordinary per-dataset scoring.
- First-use model access can require browser or token-based license acceptance.

## Bundled references

- `references/package-overview.md` — package scope, public objects, and route summary.
- `references/installation.md` — install and first-use access notes.
- `references/configuration.md` — environment variables and setting objects.
- `references/model-overview.md` — model versions and cache/version behavior.
- `references/troubleshooting.md` — cross-cutting failures that are not specific to one sub-skill.
- `references/repo-provenance.md` — source commit and refresh baseline.
- `references/repo-routing-metadata.json` — router metadata for managed import workflows.

## Bundled scripts

- `scripts/check_tabpfn_environment.py` — safe environment snapshot and import check.
- The sub-skill scripts provide focused smoke checks for APIs, preprocessing, batched inference, tuning templates, and model persistence.

## If you are unsure

Read the top-level package overview first. Then move to the narrowest
sub-skill that owns the workflow, and only cross-link when the task spans
multiple workflows.
