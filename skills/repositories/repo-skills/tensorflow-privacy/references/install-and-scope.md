# Install and scope

## Purpose

Read this before choosing a route or trying to run the package. It records the verified minimum runtime, the published package names, and the optional paths that were intentionally left out of the minimum environment.

## Verified minimum environment

- Python 3.11
- CPU-only TensorFlow 2.15 stack
- Repo runtime dependencies from `requirements.txt`
- Editable local checkout or published package install

The verified CPU runtime is enough for the core workflows in this skill:

- DP training
- privacy accounting
- DPQuery mechanics
- membership inference / secret-sharer analysis
- fast gradient clipping core helpers

## Public package names

The repo is published in two package forms:

- `tensorflow-privacy`
- `tensorflow-empirical-privacy`

The import tree is still `tensorflow_privacy`.

## Recommended installs

Published-package route:

```bash
pip install tensorflow-privacy tensorflow-empirical-privacy
```

Checkout route:

```bash
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

## Minimal import check

```bash
python -I -c "import tensorflow_privacy; print(tensorflow_privacy.__version__)"
```

## Scope notes

Included in the minimum verified scope:

- `tensorflow_privacy/privacy/analysis/`
- `tensorflow_privacy/privacy/dp_query/`
- `tensorflow_privacy/privacy/optimizers/`
- `tensorflow_privacy/privacy/keras_models/`
- `tensorflow_privacy/privacy/estimators/`
- `tensorflow_privacy/privacy/logistic_regression/`
- `tensorflow_privacy/privacy/privacy_tests/`
- `tensorflow_privacy/privacy/fast_gradient_clipping/` core helpers
- `tensorflow_privacy/privacy/sparsity_preserving_noise/`
- `tutorials/` and `g3doc/guide/` as distilled workflow evidence

Excluded from the minimum verified scope:

- `research/` archives
- `pip_tools/` maintainer scripts
- docs build scripts
- notebook / codelab executions that require external downloads or extra compatibility work
- optional NLP/BERT helper paths in fast clipping

## Optional helper paths

Some fast-clipping NLP/BERT helpers depend on `tensorflow_models`, `tensorflow_hub`, and a TensorFlow-DS/metadata stack that was not part of the minimum verified environment. Treat those paths as optional and unverified unless you explicitly prepare that extra dependency set.
