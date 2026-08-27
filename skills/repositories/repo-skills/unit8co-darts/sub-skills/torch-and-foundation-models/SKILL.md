---
name: torch-and-foundation-models
description: "Use Darts PyTorch forecasting models and foundation wrappers with
  explicit backend, checkpoint, and cache/download boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Torch and foundation models

Use this sub-skill when the user needs Darts neural forecasting models, `darts[torch]`, PyTorch Lightning trainer kwargs, CPU/GPU verification, checkpoints, or foundation model wrapper planning.

## Read first

- [`references/backend-and-training.md`](references/backend-and-training.md) for install checks, CPU/GPU/TPU boundaries, trainer kwargs, chunk lengths, and checkpoint discipline.
- [`references/model-overview.md`](references/model-overview.md) for torch/foundation model family routing and optional dependencies.
- [`references/workflows.md`](references/workflows.md) for tiny CPU `TCNModel` patterns and staged backend escalation.
- [`references/troubleshooting.md`](references/troubleshooting.md) for torch import, CUDA, covariates/chunks, checkpoints, and foundation cache/no-network failures.
- [`scripts/torch_model_smoke.py`](scripts/torch_model_smoke.py) for safe import/model-construction and optional one-epoch CPU training smoke.

## Route by task

- **Install or validate neural Darts**: check `darts[torch]`, `torch`, and `pytorch_lightning`; run `torch_model_smoke.py` before real training.
- **Tiny CPU prototype**: use small `input_chunk_length`, `output_chunk_length`, `n_epochs`, and CPU `pl_trainer_kwargs`.
- **GPU/TPU request**: verify the exact backend in the target environment. CPU torch import is not GPU proof.
- **Covariates for neural models**: validate spans in `../data-processing-and-covariates/`, then map them to model-specific chunk/covariate support here.
- **Foundation wrappers**: require explicit local cache/model path or approved network downloads before constructing wrappers that may fetch weights.
- **Metrics or explainability**: route forecast evaluation to `../evaluation-and-explainability/`.

## Safe check

```bash
python scripts/torch_model_smoke.py          # imports and constructs a tiny CPU TCNModel
python scripts/torch_model_smoke.py --train  # optional one-epoch generated-data CPU training smoke
```

Use an explicit temporary or user-approved work directory for checkpoints/logs. Do not write training artifacts into the skill directory.

## Boundaries

This sub-skill documents optional CUDA/foundation behavior but the baseline verification only proved CPU torch. Do not claim accelerator or foundation model execution until separately verified with the required hardware, wheel, cache, and memory in the user's environment.
