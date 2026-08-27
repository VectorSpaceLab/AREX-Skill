---
name: advanced-extensions
description: "Use Modin experimental Batch Pipeline, XGBoost, spreadsheet,
  NumPy, Polars, sklearn, and torch extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Modin advanced and experimental extensions

Use this sub-skill when a task names `modin.experimental`, Batch Pipeline, Modin XGBoost, spreadsheet UI, Modin NumPy, Modin Polars, experimental sklearn, or the experimental PyTorch DataLoader.

## Start here

1. Read [references/batch-pipeline.md](references/batch-pipeline.md) for `PandasQueryPipeline`, Ray-only execution, output IDs, postprocessors, fan-out, and partition-callback rules.
2. Read [references/xgboost.md](references/xgboost.md) for Ray-only distributed XGBoost, `DMatrix`, `train`, feature metadata, and dependency compatibility.
3. Read [references/experimental-frontends.md](references/experimental-frontends.md) for spreadsheet, Modin NumPy, Modin Polars, experimental sklearn, and PyTorch DataLoader boundaries.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for version-sensitive optional dependency failures and Ray-only extension errors.
5. Run [scripts/batch_pipeline_smoke.py](scripts/batch_pipeline_smoke.py) to verify a tiny Ray Batch Pipeline workflow.
6. Run [scripts/xgboost_smoke.py](scripts/xgboost_smoke.py) only after verifying the installed XGBoost package exposes Modin's required legacy Rabit APIs.

## Routing boundaries

This sub-skill owns experimental APIs and optional frontends. Route stable DataFrame/Series work to `../core-pandas-api/SKILL.md`, engine/resource setup to `../engines-configuration/SKILL.md`, and experimental file/conversion work to `../io-interoperability/SKILL.md`.

## Operating pattern

1. Treat every API here as version-sensitive. Verify imports and a tiny local fixture first.
2. Configure the Ray engine before importing Modin for Batch Pipeline or XGBoost.
3. Keep optional dependencies explicit: `xgboost`, `scikit-learn`, `modin-spreadsheet`, `polars`, and `torch` are not all covered by the base package.
4. Do not scale training, UI, or network-dependent workflows until the bundled smoke or a local equivalent passes.
5. Carry import or dependency incompatibilities as optional extension caveats rather than claiming stable package coverage.
