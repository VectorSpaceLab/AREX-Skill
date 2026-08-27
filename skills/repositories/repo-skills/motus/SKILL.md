---
name: motus
description: "Use Motus, a unified latent-action world model, for
  robot-video/action data preparation, CUDA inference, RoboTwin evaluation, and
  distributed training configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Motus repository skill

Motus combines a WAN video generator, action expert, and frozen Qwen VLM in a
trimodal mixture-of-tokens model for robot video, actions, and latent-action
pretraining. Use this skill for operational work around the public Motus
repository; it does not replace the external RoboTwin simulator or supply model
checkpoints and datasets.

## Route by task

- **Data layouts, episode validation, camera views, normalization, conversion,
  or LeRobot/T5 caches:** read [data-preparation](sub-skills/data-preparation/SKILL.md).
- **Real-world image inference, T5 conditioning, checkpoints, or RoboTwin
  policy evaluation:** read [model-inference](sub-skills/model-inference/SKILL.md).
- **YAML configuration, fine-tune/resume semantics, torchrun, DeepSpeed, SLURM,
  or checkpoint export:** read [training](sub-skills/training/SKILL.md).

Read [troubleshooting](references/troubleshooting.md) for cross-cutting
installation, assets, optional backends, and path failures. Read
[provenance](references/repo-provenance.md) before deciding whether this skill
matches a changed Motus checkout.

## Installation and prerequisites

The source documents Python 3.10, CUDA 12.8, torch 2.7.1/torchvision 0.22.1,
`flash-attn`, and the pinned runtime requirements. Install a compatible CUDA
wheel first, then the requirements needed by the selected route. LeRobot adds
its own optional package and requirements. Use an isolated environment; do not
install all optional assets merely to inspect the routing skill.

Minimal import smoke:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -c "from data.dataset import create_dataset, collate_fn; from models.action_expert import ActionExpertConfig; print(ActionExpertConfig())"
```

Actual model construction, checkpoint loading, T5 encoding, training, and
RoboTwin execution require CUDA, large external assets, and substantial VRAM.
The public guide estimates over 24 GB for pre-encoded-T5 inference, about 41 GB
for on-the-fly T5, and over 80 GB for training. Treat CPU imports and `--help`
checks as parser/API evidence only.

## Shared operating rules

1. Replace all example paths with paths valid on the target machine. Keep WAN,
   VLM, VAE, checkpoint, dataset, and output roots distinct and readable.
2. Derive `action_chunk_size` from the common frame count and video/action
   frequency ratio; keep action dimensions, state dimensions, embodiment config,
   and normalization statistics aligned.
3. Prefer pre-encoded language embeddings when memory is constrained. Keep the
   selected text instruction aligned with its embedding variant.
4. Run safe validation before any network download, cache rewrite, simulator
   launch, or distributed job. Launches are explicit, potentially expensive
   operations and are never inferred from an import success.
