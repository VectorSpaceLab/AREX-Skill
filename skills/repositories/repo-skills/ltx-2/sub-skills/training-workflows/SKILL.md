---
name: training-workflows
description: "Guides LTX Trainer mode selection, config editing, safe launch
  planning, monitoring, resume, LoRA or full fine-tuning, and training
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LTX Training Workflows

Use this sub-skill when a user asks to train, fine-tune, resume, configure, monitor, debug, or plan an LTX-2/LTX-2.3/LTX-2.5 LoRA or full fine-tune. It covers LTX Trainer workflows that use the `ltx_trainer` package, the flexible training strategy, YAML configs, `uv`, and Accelerate.

## Route Here When

- The task mentions training, fine-tuning, LoRA, IC-LoRA, full fine-tune, trainer YAML, `training_strategy`, `is_generated`, target modules, checkpoints, resume, W&B, Hub upload, or training validation samples.
- The user needs to choose between T2V, I2V, V2V IC-LoRA, A2V, V2A, T2A, A2A, AV2AV, extension, inpainting, outpainting, LoRA, or full fine-tuning.
- The user has a config validation error, missing model path/component path, unsupported condition, stale embeddings after a model-version switch, OOM during training or validation, or a confusing resume outcome.
- The user wants a safe command to launch later but has not approved running expensive training yet.

## Route Elsewhere

- Raw media organization, metadata columns, reference media generation, masks, captioning, scene splitting, latent preprocessing, and stale `.precomputed` reconciliation belong in [data-preparation](../data-preparation/SKILL.md).
- Running inference with a trained LoRA or full checkpoint belongs in [inference-pipelines](../inference-pipelines/SKILL.md).
- CUDA/NATTEN/Triton/FlashAttention/kernel installation, quantization backends, and hardware backend choices belong in [performance-backends](../performance-backends/SKILL.md).
- Core model architecture questions belong in [core-components](../core-components/SKILL.md).

## Safe Operating Rules

1. Do not claim that a dataset will be sufficient, that quality will improve, or that a particular number of steps will produce a certain result. Report only configuration facts, observed metrics, user choices, and documented constraints.
2. Do not launch captioning, preprocessing, training, Hub pushes, or long validation without explicit user approval for that action.
3. Treat dataset preparation as a prerequisite and route it to `data-preparation` unless the user already has a verified `preprocessed_data_root`.
4. Keep run-specific configs and outputs in a user-approved run workspace. Do not edit shipped template configs unless the task is explicitly repo maintenance.
5. When the requested behavior cannot be represented by `training_strategy.name: "flexible"` plus existing conditions, use the custom-strategy escape hatch; do not silently patch trainer internals.

## Workflow

1. **Identify intent and mode.** Use [references/training-modes.md](references/training-modes.md) to map the user request to a flexible strategy, generated/frozen modalities, condition blocks, target-module family, and validation condition shape.
2. **Confirm prerequisites.** Check that the user has local model components, a matching text encoder, a preprocessed dataset, GPU/backend readiness, output workspace, checkpoint/resume intent, and authorization for any expensive step.
3. **Patch the config safely.** Use [references/configuration.md](references/configuration.md) for exact schema sections, split/unified checkpoint path rules, LoRA target modules, optimization, acceleration, validation, checkpoint, Hub, W&B, and flow-matching fields.
4. **Validate before launch.** Run the bundled validator from any directory:

   ```bash
   python path/to/training-workflows/scripts/validate_training_config.py /path/to/config.yaml
   ```

   Use `--relaxed-paths` only while placeholders are still being filled; strict validation is required before a real launch.
5. **Build the launch command.** Use the command builder without executing training:

   ```bash
   python path/to/training-workflows/scripts/build_training_command.py /path/to/config.yaml --distributed none
   python path/to/training-workflows/scripts/build_training_command.py /path/to/config.yaml --distributed ddp --num-processes 2 --disable-progress-bars
   ```

6. **Launch only after approval.** Follow [references/launch-monitor-resume.md](references/launch-monitor-resume.md) for single-GPU, Accelerate, DDP/FSDP, W&B, Hub, checkpoint, resume, and monitoring behavior.
7. **Recover from problems.** Use [references/troubleshooting.md](references/troubleshooting.md) for symptoms and safe fixes. If the problem is unsupported training logic, read [references/custom-strategies.md](references/custom-strategies.md) and ask before code changes.
8. **Hand off after training.** For production or qualitative inference with trained LoRAs, route to `inference-pipelines`. Training-time validation samples are monitoring signals, not a final quality claim.

## Bundled References and Helpers

- [references/training-modes.md](references/training-modes.md): mode table, flexible strategy semantics, target-module families, and training-to-validation condition mapping.
- [references/configuration.md](references/configuration.md): practical YAML schema guide and safe patching checklist.
- [references/launch-monitor-resume.md](references/launch-monitor-resume.md): explicit launch commands, Accelerate variants, monitoring, W&B/Hub, checkpoint, resume, and no-resume behavior.
- [references/custom-strategies.md](references/custom-strategies.md): when config is enough, when custom code is justified, and how to modify trainer strategy code safely after consent.
- [references/troubleshooting.md](references/troubleshooting.md): config, path, model-version, OOM, validation, credential, and resume recovery matrix.
- [scripts/validate_training_config.py](scripts/validate_training_config.py): safe YAML/Pydantic validation helper with strict path checks or relaxed placeholder mode; never launches training.
- [scripts/build_training_command.py](scripts/build_training_command.py): prints single-GPU or Accelerate commands; never executes them.
- [scripts/launch_training.py](scripts/launch_training.py): bundled self-contained trainer launcher to run only after validation and explicit approval.
- [references/accelerate/ddp.yaml](references/accelerate/ddp.yaml), [references/accelerate/ddp_compile.yaml](references/accelerate/ddp_compile.yaml), [references/accelerate/fsdp.yaml](references/accelerate/fsdp.yaml), and [references/accelerate/fsdp_compile.yaml](references/accelerate/fsdp_compile.yaml): bundled Accelerate presets used by the command builder for named distributed launch modes.
