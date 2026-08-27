---
name: training-and-models
description: "Use Towhee's optional PyTorch Trainer, TrainingConfig YAML,
  NNOperator training bridge, and towhee.models package boundaries safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Towhee training and models

Use this sub-skill when the task involves Towhee's optional PyTorch training layer: `TrainingConfig`, `Trainer`, `NNOperator.train(...)`, `NNOperator.setup_trainer(...)`, checkpoint/model-card behavior, or deciding whether to install `towhee.models` instead of using Hub operators.

## Fast routing

- For `TrainingConfig` fields, YAML save/load shape, device choices, loss/optimizer/scheduler names, `Trainer`, and `NNOperator` training, use [Training configuration and Trainer](references/training-config.md).
- For the `towhee.models` package split, `create_model(...)` pattern, pretrained-download risk, and Hub-versus-model-zoo decisions, use [Model-zoo boundaries](references/model-zoo-boundaries.md).
- For optional PyTorch/TorchVision/TorchMetrics installs, Towhee auto-install side effects, missing trainable model attributes, CUDA/CPU device mistakes, and model-download failures, use [Troubleshooting](references/troubleshooting.md).
- To produce a CPU-safe config stub without importing Towhee or torch, run [training_config_template.py](scripts/training_config_template.py). Add `--check-imports` only in an isolated environment where importing the optional trainer stack is acceptable.

## Boundaries and handoff

- Stay here for high-level training configuration, `Trainer` setup, `NNOperator` training hooks, checkpoint/model-card expectations, and model-zoo installation boundaries.
- Route custom pipeline operators, `ops`, `register`, Hub revisions, and `towhee init` to [operator-hub-and-cli](../operator-hub-and-cli/SKILL.md).
- Route `DataCollection`, `DataLoader`, image/audio/video wrappers, and non-training data serialization to `data-utilities`.
- Route HTTP/GRPC services, `towhee server`, Docker, Triton, and deployment packaging to `serving-and-triton`.
- Do not use this sub-skill as an exhaustive per-model API catalog. Treat large model tests, pretrained downloads, and full fine-tuning runs as explicit user-approved optional work.

## Default safe workflow

```bash
python scripts/training_config_template.py --format yaml --output training_config.yaml
```

Start with `device_str: cpu`, `dataloader_num_workers: 0`, `tensorboard: null`, and `pretrained=False` model choices when the user only needs a portable template or diagnosis. Move to actual training only after the active environment has the intended PyTorch stack and any model/data downloads are approved.
