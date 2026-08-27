---
name: model-operations
description: "Operate PyOD model persistence, thresholding, score combination,
  optional extras, and validation safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# PyOD Model Operations

Use this sub-skill when a PyOD task is about operating fitted detectors after or around training: saving and loading models, validating recovered artifacts, choosing non-contamination thresholders, combining multiple detector scores, enabling optional operational extras, and diagnosing model-operation failures.

Route detector selection, baseline fit/predict recipes, and tabular model-family choice to `classic-detectors` or `automated-lifecycle`. Route graph, time-series, embedding, audio, and deep-backend constraints to `specialized-modalities` before applying persistence or operational validation guidance here.

## Operating Rules

1. Treat every pickle/joblib artifact as executable code. Use `pyod.utils.persistence.load(..., trusted=True)` or `compat_load(..., trusted=True)` only for artifacts from a trusted training pipeline, registry, or owner. `trusted=True` is an acknowledgement, not a scan or sandbox.
2. Prefer `pyod.utils.persistence.save` / `load` for new artifacts. Raw `joblib.dump` / `joblib.load` is a fallback only when you intentionally need the raw format and accept the missing envelope metadata.
3. Validate a loaded model before use: check the class, fitted attributes, score shape, finite scores, and at least one known probe batch if available.
4. Install optional extras explicitly and exactly. Base PyOD does not install `combo`, `pythresh`, `suod`, or `xgboost`; failures in those areas are usually dependency-scope failures, not detector logic failures.
5. Standardize detector-score matrices before using score-combination functions unless the scores are already on a deliberately comparable scale.

## Bundled References and Scripts

- [references/persistence.md](references/persistence.md): use for `save`, `load`, `compat_load`, trust boundaries, sklearn Tree dtype compatibility, metadata, strict mode, and raw joblib caveats.
- [references/thresholding-and-combination.md](references/thresholding-and-combination.md): use for `pyod.models.thresholds`, PyThresh-backed contamination objects, `pyod.models.combination`, required score shapes, and validation checks.
- [references/optional-extras.md](references/optional-extras.md): use when imports fail or a task asks for SUOD acceleration, XGBOD supervised operation, combo score combination, or pythresh thresholding.
- [references/troubleshooting.md](references/troubleshooting.md): use to map operational symptoms to recovery actions for persistence, thresholding, combination, optional extras, and post-load validation.
- [scripts/persistence_smoke.py](scripts/persistence_smoke.py): safe deterministic smoke check that fits a tiny detector, saves and loads it through PyOD persistence, verifies the trust guard, compares predictions, and writes only a temporary file.

## Quick Safe Checks

Run the bundled script from any working directory in an environment with PyOD installed:

```bash
python scripts/persistence_smoke.py --help
python scripts/persistence_smoke.py --json
```

A passing run proves the local PyOD install can perform a trusted temporary persistence round-trip for a classic detector. It does not prove that an arbitrary external artifact is safe, compatible, or semantically valid.
