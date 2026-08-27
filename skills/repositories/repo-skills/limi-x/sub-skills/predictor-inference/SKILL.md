---
name: predictor-inference
description: "Use LimiXPredictor for local checkpoint inference on tabular
  classification, regression, and missing-value imputation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Predictor Inference

Use this sub-skill when a task needs the direct Python API for LimiX tabular inference with `inference.predictor.LimiXPredictor`: single-dataset classification, regression, or missing-value imputation (MVI) using a local LimiX checkpoint and local inference configuration.

## Immediate routing

- For constructor arguments, `predict()` returns, config-list caveats, CPU constraints, and DDP handoff, read [API reference](references/api-reference.md).
- For copy-adaptable classification, regression, and MVI recipes, read [workflows](references/workflows.md).
- For accepted array/dataframe shapes, targets, categorical/object columns, NaN handling, and size guidance, read [data formats](references/data-formats.md).
- For common failures and fixes, read [troubleshooting](references/troubleshooting.md).
- To validate imports, a local config, tiny fixture shapes, and optional full inference without downloading anything, use [scripts/predictor_smoke_template.py](scripts/predictor_smoke_template.py).
- To generate a deterministic MVI mask and score reconstruction errors on tiny arrays, use [scripts/mvi_mask_fixture.py](scripts/mvi_mask_fixture.py).

## Scope

This sub-skill covers direct `LimiXPredictor` API usage only. The predictor loads the checkpoint in its constructor, so full checkpoint inference requires a local `.ckpt` file. CUDA/GPU may be required for practical full inference, retrieval configs, flash-attention paths, or DDP; CPU use is limited to non-retrieval configs and automatically disables mixed precision.

## Route out of this sub-skill

- Benchmark-style loops over dataset directories, batch result files, and CLI wrappers belong to [benchmark-cli](../benchmark-cli/SKILL.md).
- Authoring or inspecting inference configuration pipelines, feature transforms, and preprocessing choices belongs to [configuration-preprocessing](../configuration-preprocessing/SKILL.md).
- Retrieval hyperparameter search, retrieval parameter tuning, and Optuna-style search belongs to [retrieval-optimization](../retrieval-optimization/SKILL.md).

## Operating checklist

1. Confirm the caller has a local LimiX checkpoint path and a local JSON config path or in-memory config list.
2. Pick a config compatible with task and device: no retrieval on CPU; MVI uses `mask_prediction=True` and an MVI/non-retrieval regression config.
3. Validate input shapes and target type before constructing the predictor.
4. Instantiate `LimiXPredictor`, then call `predict()` with exact task type string `"Classification"` or `"Regression"`.
5. Interpret output by task: classification returns NumPy probabilities, regression returns a torch tensor, and MVI returns a tuple with reconstructed features.
