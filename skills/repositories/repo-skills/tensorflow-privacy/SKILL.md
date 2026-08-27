---
name: tensorflow-privacy
description: "Routes TensorFlow Privacy users who need differentially private
  training, privacy accounting, query mechanisms, empirical privacy tests, or
  fast gradient clipping."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TensorFlow Privacy

Use this skill for TensorFlow Privacy workflows: DP-SGD training, privacy-budget accounting, lower-level DP queries, membership inference and secret-sharer analysis, and fast gradient clipping.

## Start here

Read `references/install-and-scope.md` before installing or choosing a route. It captures the minimum verified CPU-only environment, the published package names, and the optional paths that are out of scope for the default runtime.

Run `scripts/check_env.py` when you want a quick import and smoke check against an installed environment.

Read `references/repo-provenance.md` when you need to check whether this skill matches the current TensorFlow Privacy checkout, or before refreshing the skill after repo drift.

## Route map

- `sub-skills/training/` — differentially private training with optimizers, Keras model wrappers, estimators, and logistic regression helpers.
- `sub-skills/privacy-accounting/` — epsilon, delta, and noise-multiplier calculations plus the privacy accounting CLIs.
- `sub-skills/queries/` — lower-level `DPQuery` stacks, Gaussian/discrete/Skellam mechanisms, and tree aggregation query helpers.
- `sub-skills/privacy-tests/` — membership inference, privacy reports, callbacks, and secret-sharer exposure analysis.
- `sub-skills/fast-clipping/` — fast gradient clipping, layer registries, and sparse-noise helpers.

## Package surface

The public Python package is `tensorflow_privacy`. The repo also ships empirical privacy-test modules under the same import tree.

Typical install choices:

- Published packages: `pip install tensorflow-privacy tensorflow-empirical-privacy`
- Working from a checkout: install the repo's runtime requirements first, then editable install the root package

Minimal import check:

```bash
python -I -c "import tensorflow_privacy; print(tensorflow_privacy.__version__)"
```

If you want a slightly stronger check, inspect the public privacy-accounting helper too:

```bash
python -I -c "from tensorflow_privacy.privacy.analysis import compute_dp_sgd_privacy_lib as cdp; print(cdp.compute_dp_sgd_privacy_statement)"
```

## How to choose a sub-skill

If the task is about training a differentially private model, start with `training`.
If the task is about epsilon/noise calculation or the privacy CLI flags, start with `privacy-accounting`.
If the task is about custom mechanisms or DPQuery internals, start with `queries`.
If the task is about membership inference, privacy reports, or secret sharing, start with `privacy-tests`.
If the task is about faster clipping or sparse-noise internals, start with `fast-clipping`.

## Cross-cutting caution

This skill's minimum verified environment is CPU-only. GPU or TPU helpers are optional and should only be claimed when the user explicitly asks for them and the matching hardware and package variant are available.

Do not expect the original repository checkout to remain available at runtime. Use the bundled references and scripts inside this skill tree instead of source checkout paths.
