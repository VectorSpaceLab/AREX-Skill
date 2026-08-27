---
name: deepctr
description: "Use this DeepCTR repo skill for CTR/recommender feature columns,
  Keras models, sequence/session models, multitask models, and legacy TensorFlow
  Estimator workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepCTR

Use this repo skill when the task mentions DeepCTR, click-through-rate prediction, recommender models, sparse/dense feature columns, DIN/BST/DIEN/DSIN, multitask heads, or the legacy TensorFlow Estimator surface.

## Install and verify

DeepCTR does **not** install TensorFlow for you. Install a TensorFlow build that matches your Python and platform, then install DeepCTR:

```bash
python -m pip install "numpy<2" "tensorflow<2.21"
python -m pip install deepctr
```

If you are using a TensorFlow 2.20-style stack with legacy Keras requirements, install the matching `tf-keras` package and set `TF_USE_LEGACY_KERAS=1` before running DeepCTR. See [references/installation-and-compatibility.md](references/installation-and-compatibility.md) for compatibility notes.

Quick environment check:

```bash
python scripts/check_deepctr_env.py --json
```

## Route by need

- `data-and-feature-columns` for `SparseFeat`, `DenseFeat`, `VarLenSparseFeat`, hashing, vocabulary paths, and input schema validation.
- `keras-model-workflows` for ordinary CTR/regression models, compile/fit/predict/save/load, and model selection.
- `sequence-models` for DIN, BST, DIEN, DSIN, `hist_`/`sess_` naming, and sequence/session debugging.
- `multitask-models` for SharedBottom, ESMM, MMOE, PLE, and multi-output target packing.
- `estimator-workflows` for `tf.estimator`, TFRecord/Pandas input functions, and runtime gating.

## Read first

- [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/version/GPU issues.
- [references/repo-provenance.md](references/repo-provenance.md) when you need to check freshness or decide whether this skill is stale.

## Common starting point

If the user has not specified a model family yet, start with `data-and-feature-columns` when the problem is input shaping, otherwise `keras-model-workflows` for single-output model choice.

## What this skill does not do

- It does not tell you to open the original repository's examples or tests at runtime.
- It does not require a GPU unless the user explicitly asks for GPU or multi-GPU execution.
- It does not require Estimator workflows when `tf.estimator` is unavailable; in that case, use the Keras routes.
