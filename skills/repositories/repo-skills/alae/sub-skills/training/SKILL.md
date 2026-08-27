---
name: training
description: "Train ALAE and StyleALAE with configs, TFRecords, DDP, and checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Training

Use this sub-skill when the request is about training or resuming ALAE/StyleALAE with `train_alae.py`, YACS configs, the multi-GPU launcher, TFRecords loading, LOD scheduling, checkpoint handling, or safe command construction.

Do not use this sub-skill for raw data conversion, generation/style mixing, or metrics. The README's ablation route (`train_alae_separate.py`, `model_separate.py`, and the `celeba_ablation_*.yaml` files) is not present in this checkout; treat it as unavailable rather than routing there.

## Read first

- [Training workflow](references/training-workflow.md)
- [API reference](references/api-reference.md)
- [Checkpoint conventions](references/checkpoints.md)
- [Troubleshooting](references/troubleshooting.md)
- [Config inspector](scripts/inspect_alae_config.py)

## Typical outcomes

- Build a valid `python train_alae.py -c <config> [YACS opts...]` command.
- Check dataset, checkpoint, and output paths before starting a run.
- Diagnose GPU, DDP, TFRecords, config-key, or checkpoint mismatch issues.
