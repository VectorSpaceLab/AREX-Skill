---
name: "pypots"
description: "Routes PyPOTS workflows for imputation, forecasting,
  classification, anomaly detection, clustering, representation learning, and
  the command-line and data-management surfaces around them."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyPOTS

PyPOTS is a toolbox for machine learning on partially-observed time series.
Use this skill when the request is about missing-value handling, time-series
prediction, task-specific training, model inspection, data preparation, or the
`pypots-cli` interface.

## Start Here

- Install from PyPI: `pip install pypots`
- Install from this checkout: `pip install -e .`
- If you will use YAML configs or the CLI helpers, also install `pyyaml`.
- Optional backend packages:
  - `torch-geometric`, `torch-scatter`, `torch-sparse` for Raindrop.
  - LLM-oriented workflows may need extra tokenizer/model packages and model
    downloads.

Run the bundled [`scripts/check_install.py`](scripts/check_install.py) for a safe first check:

```bash
python scripts/check_install.py
```

That helper prints the package version, model counts, CLI command surface, and
optional backend status without training anything.

## Route Map

### [Imputation](sub-skills/imputation/SKILL.md)
Use for filling missing values with `Mean`, `Median`, `LOCF`, `Lerp`, `SAITS`,
`BRITS`, `USGAN`, `TEFN`, `TimeLLM`, and the other imputation families.
Read this route for `impute`, `predict()["imputation"]`, lazy-loading HDF5
inputs, checkpoint save/load, and evaluation with missingness masks.

### [Forecasting](sub-skills/forecasting/SKILL.md)
Use for future-value prediction with `BTTF`, `TEFN`, `TimeMixer`, `TimeLLM`,
`TimesNet`, `FITS`, `GPT4TS`, `MOMENT`, and related forecasting models.
Read this route for `forecast`, `predict()["forecasting"]`, `X_pred` inputs,
and model selection across short- and long-horizon use cases.

### [Classification](sub-skills/classification/SKILL.md)
Use for labeled time-series classification with `Raindrop`, `TS2Vec`,
`TimesNet`, `BRITS`, `CSAI`, `GRUD`, `SAITS`, `iTransformer`, `TEFN`,
`PatchTST`, and `Autoformer`.
Read this route for `classify`, `predict_proba`, class labels, and binary metric
interpretation.

### [Anomaly detection](sub-skills/anomaly-detection/SKILL.md)
Use for anomaly scoring and binary anomaly labels with `TimesNet`, `TEFN`,
`TimeMixer`, `Transformer`, `FiLM`, `SegRNN`, and the other detector families.
Read this route for `detect`, `predict()["anomaly_detection"]`, anomaly-rate
inputs, and score-to-label evaluation.

### [Clustering](sub-skills/clustering/SKILL.md)
Use for cluster assignment workflows with `CRLI` and `VaDER`.
Read this route for `cluster`, `predict()["clustering"]`, latent-variable
outputs, and external/internal cluster validation metrics.

### [Representation](sub-skills/representation/SKILL.md)
Use for time-series embeddings and vectorization with `TS2Vec`.
Read this route for `represent`, `predict()["representation"]`, and downstream
use of learned embeddings.

### [CLI and data management](sub-skills/cli/SKILL.md)
Use for `pypots-cli` workflows: `info`, `model`, `train`, `predict`,
`evaluate`, `tune`, `recommend`, `benchmark`, and `data`.
Read this route for config files, HDF5/CSV conversion, dataset profiles,
benchmark comparisons, and model inspection/config generation.

## Shared References

- [`references/model-overview.md`](references/model-overview.md) — model families, representative choices, and
  which task route owns each family.
- [`references/api-reference.md`](references/api-reference.md) — verified task bases, helper methods,
  constructor patterns, return keys, and optimizer wrappers.
- [`references/data-formats.md`](references/data-formats.md) — HDF5/CSV schemas, `BaseDataset` sample order,
  and the programmatic data-utility surface.
- [`references/cli-reference.md`](references/cli-reference.md) — command groups, flags, config shapes, and
  CLI-specific gotchas.
- [`references/troubleshooting.md`](references/troubleshooting.md) — install/import problems, backend gaps,
  shape/key mismatches, and CLI/data failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) — source commit and refresh baseline.

## Usage Notes

- Most models accept in-memory dicts or HDF5 file paths.
- All task routes rely on the shared `pypots.data` and `pypots.nn.functional`
  contracts described in the references above.
- Use CPU by default; switch to CUDA only when you want acceleration and the
  environment has a compatible GPU.
- If a request names `TimeSeriesAI`, treat it as a separate service-oriented
  surface unless the user explicitly wants the local PyPOTS package.

## Before You Refresh

Check [`references/repo-provenance.md`](references/repo-provenance.md) against the current checkout before using
this skill on a newer PyPOTS revision. If the commit, dirty state, or package
version changed, refresh the skill instead of assuming these routes are current.
