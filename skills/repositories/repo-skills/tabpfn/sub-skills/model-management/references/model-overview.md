# Model Overview

## Version families

- `v2` — legacy family with direct download support.
- `v2.5` — gated family with model-card/license checks.
- `v2.6` — gated family with model-card/license checks.
- `v3` — current default family.

## What resolves a model path

- `model_path='auto'` uses the default checkpoint for the selected version.
- A bare filename is first checked relative to the current working directory and
  then relative to the cache directory.
- A list of paths is allowed when the estimator should use multiple models.
- A model-spec object can be passed when the caller already built the model.

## Model source behavior

- The package knows the correct model source repository for each version and task.
- `download_model` tries the HuggingFace source first and may fall back to a direct
  URL for the older family that supports it.
- `download_all_models` fetches the full model set into the cache directory.

## When to route questions here

Use this file for version selection, path resolution, and the high-level meaning
of `model_path`. Use model-weights for access control and model-management for
actual download and persistence workflows.
