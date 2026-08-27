---
name: training
description: "Configure, launch, and troubleshoot Dexbotic VLA supervised
  fine-tuning, LoRA, and distributed training backends."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Dexbotic training

Use this route for experiment composition, model/data/trainer configuration, SFT, LoRA, checkpoint lineage, and DDP/DeepSpeed/FSDP backend selection. Start with [training workflow](references/workflows.md), then validate the selected backend with [backend resolution](references/backend-resolution.md). Route dataset schema/conversion to [data-preparation](../data-preparation/SKILL.md) and serving/evaluation to the corresponding sibling skills.

## Safe operating sequence

1. Confirm the checkpoint family, action dimension, camera count/order, state convention, dataset name, output directory, and whether the job is SFT or LoRA.
2. Run `scripts/inspect_training_config.py` against a copied/minimal config or JSON/YAML fragment. It checks required keys and backend compatibility without launching training.
3. Select exactly one `train_backend`: `ddp`, `deepspeed`, `fsdp`, or `fsdp2`. Do not infer a backend from installed packages; use the resolver contract and explicit config.
4. Match normalization stats and action transforms to the dataset. Keep `norm_stats.json` with the checkpoint or record its deliberate external location.
5. Use `torchrun`/the documented launcher only after a one-batch or one-step plan is approved. Full training, model downloads, and distributed jobs are not safe verification defaults.
6. For LoRA recipes, honor the entrypoint's backend restrictions; the documented Libero LoRA recipes use DDP and reject DeepSpeed/FSDP.

The core claims require a CUDA-capable PyTorch runtime. CPU imports can validate configuration code but cannot validate VLA training behavior.
