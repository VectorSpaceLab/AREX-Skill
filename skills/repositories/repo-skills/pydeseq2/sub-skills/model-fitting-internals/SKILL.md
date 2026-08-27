---
name: model-fitting-internals
description: "Inspect and control PyDESeq2 staged model-fitting internals,
  normalization helpers, VST, AnnData storage keys, Cooks refits, and
  DefaultInference behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyDESeq2 Model-Fitting Internals

Use this sub-skill when an agent must inspect, debug, or manually control PyDESeq2's staged internals instead of only running the high-level `DeseqDataSet.deseq2()` wrapper.

## Use When

- You need the exact staged order for `fit_size_factors`, dispersion fitting, MAP shrinkage, LFC fitting, Cooks distances, and outlier refits.
- You need to inspect where PyDESeq2 stores fitted values in `obs`, `var`, `varm`, `layers`, `obsm`, and `uns`.
- You need leakage-safe train/test normalization with `deseq2_norm_fit` and `deseq2_norm_transform`.
- You need to diagnose `vst`, `vst_fit`, or `vst_transform` failures and choose blind versus design-aware VST.
- You need to reason about `DefaultInference`, `n_cpus`, joblib backends, or `low_memory` side effects.

## Read First

- `references/internals-reference.md` for staged fitting order, method responsibilities, storage keys, and inference behavior.
- `references/vst-and-normalization.md` for size-factor modes, control genes, preprocessing helpers, VST order, and train/test patterns.
- `references/troubleshooting.md` for actionable fixes for common internals failures and warnings.

## Bundled Scripts

- `scripts/inspect_stepwise_pipeline.py` runs a local synthetic stepwise fit with `--n-cpus 1` by default and prints expected AnnData keys after each stage.
- `scripts/check_normalization.py` demonstrates `deseq2_norm_fit` on training counts and `deseq2_norm_transform` on held-out counts without network access.

Example commands:

```bash
python scripts/inspect_stepwise_pipeline.py --help
python scripts/inspect_stepwise_pipeline.py --n-cpus 1 --use-design-vst
python scripts/check_normalization.py --help
python scripts/check_normalization.py --as-json
```

If PyDESeq2 is missing, install it with a generic package command such as `python -m pip install pydeseq2` in the active Python environment.

## Routing Boundaries

- For standard end-to-end differential expression analysis with `DeseqDataSet.deseq2()` and `DeseqStats`, route to `../dea-workflows/SKILL.md`.
- For count/metadata schemas, CSV loading, AnnData construction, and validation failures, route to `../data-io-validation/SKILL.md`.
- For contrasts, p-values, adjusted p-values, LFC shrinkage, result tables, and plots, route to `../statistics-and-results/SKILL.md`.

## Safe Defaults

- Prefer `DefaultInference(n_cpus=1)` in examples and verification unless the user explicitly asks to parallelize.
- Prefer `fit_type="parametric"` for DESeq2-like defaults, but switch to `fit_type="mean"` when parametric trend fitting repeatedly falls back or the user asks for the mean trend.
- Prefer `size_factors_fit_type="ratio"` when geometric means are valid; use `"poscounts"` for sparse positive-count settings and `"iterative"` only when the staged MLE behavior is intended.
- For train/test workflows, fit ratio log means on training counts and transform held-out counts; do not recompute normalization facts on test counts unless the user explicitly accepts leakage.
