---
name: analysis-and-persistence
description: "MatrixProfile, STUMPY-backed alternatives, and estimator
  round-tripping via JSON, Pickle, and HDF5."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# analysis-and-persistence

Use this sub-skill for `tslearn.matrix_profile` and persistence work.

Stay here when the task asks you to:
- compare `MatrixProfile` implementations (`numpy`, `stump`, optional `gpu_stump`)
- serialize or reload fitted tslearn estimators with `BaseModelPackage`
- reason about `tslearn.hdftools` and HDF5-backed round-trips

Route elsewhere when the task is mainly about:
- metric derivations or backend selection: [metrics-backends](../metrics-backends/SKILL.md)
- clustering workflows: [clustering](../clustering/SKILL.md)
- supervised learning: [supervised-models](../supervised-models/SKILL.md)
- forecasting: [forecasting](../forecasting/SKILL.md)
- data loading, scaling, or feature prep: [data-preparation](../data-preparation/SKILL.md)

Rules of thumb:
- Treat `numpy` as the reference path for MatrixProfile correctness.
- Treat `stump` as the CPU acceleration path that should match `numpy` on the same tiny univariate series when `stumpy` is installed.
- Treat `gpu_stump` as optional acceleration only; do not make it the baseline check.
- Use JSON and Pickle without `h5py`.
- Use HDF5 only when `h5py` is installed.
- Expect unfitted estimators to raise `NotFittedError` on `to_*`.
- Keep matrix-profile inputs univariate for the bundled checks.

Start with:
- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke script](scripts/analysis_smoke.py)

If you need to expand beyond this scope, hand off through the [root router](../../SKILL.md).
