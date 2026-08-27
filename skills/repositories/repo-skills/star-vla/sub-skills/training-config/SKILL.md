---
name: training-config
description: "Plan StarVLA training, co-training, YAML overrides, DeepSpeed
  launches, checkpoints, and safe validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StarVLA training-config

Use this sub-skill when the user needs a safe StarVLA training or co-training launch plan, wants to edit an OmegaConf YAML, needs to reason about CLI dotlist overrides, or is debugging trainer/checkpoint behavior before running a GPU job.

## Start here

1. Identify the intended entry point:
   - VLA-only policy training: `starVLA/training/train_starvla.py`.
   - VLA + VLM co-training: `starVLA/training/train_starvla_cotrain.py`.
   - VLM-only tuning: `starVLA/training/train_starvlm.py`.
2. Read the base YAML and apply command-line overrides as `KEY=VALUE` dotlist items after the YAML.
3. Plan the `accelerate launch` command without running it. Use [scripts/plan_training_command.py](scripts/plan_training_command.py) for a safe dry-run command plan.
4. Check output layout: StarVLA sets `output_dir = run_root_dir/run_id`, writes checkpoints under `checkpoints/`, and writes final weights under `final_model/`.
5. For common failures, use [references/troubleshooting.md](references/troubleshooting.md) before escalating to environment or model-family debugging.

## References

- [Configuration reference](references/configuration-reference.md): YAML sections, OmegaConf precedence, Accelerate/DeepSpeed configs, checkpoint directories.
- [Training workflows](references/training-workflows.md): entry-point choice, launch anatomy, W&B-disable hints, safe validation, reference-only source launchers.
- [Trainer API](references/trainer-api.md): `TrainerUtils`, learning-rate groups, `freeze_modules`, dotlist normalization, checkpoint save/reload behavior.
- [Troubleshooting](references/troubleshooting.md): bad override syntax, horizon/data mismatch, dataset statistics, W&B, distributed, DeepSpeed/GPU, and flash-attn issues.

## Route elsewhere

- Model architecture family, framework registry names, action heads, and checkpoint/model compatibility: [model-frameworks](../model-frameworks/SKILL.md).
- Dataset registry creation, LeRobot layout, `data_mix`, `dataset_py`, modality JSON, and data indices: [data-integration](../data-integration/SKILL.md).
- Benchmark evaluation after a checkpoint exists: [benchmark-evaluation](../benchmark-evaluation/SKILL.md).
- Serving checkpoints or policy-server config overrides: [policy-deployment](../policy-deployment/SKILL.md).
- Cross-cutting install/backend failures: [root troubleshooting](../../references/troubleshooting.md).

## Operating rules

- Do not launch training unless the user explicitly asks for execution and the required backend is prepared. Training entry points use CUDA autocast and common recipes assume GPUs plus Accelerate/DeepSpeed.
- Prefer explicit `KEY=VALUE` overrides, for example `framework.name=QwenGR00T` and `trainer.freeze_modules=`. Avoid bare flags when the intended value is empty.
- Do not copy source `run_*.sh` launchers as-is. Treat them as reference-only because they set site-specific NCCL interfaces, GPU counts, data/model paths, and W&B identities.
