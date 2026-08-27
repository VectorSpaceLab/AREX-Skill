---
name: generation-pipeline
description: "Plan DreamCraft3D staged generation commands, configs, checkpoint
  chaining, and launch troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Generation Pipeline

Use this sub-skill when a task is about running or adapting DreamCraft3D's canonical staged optimization pipeline: coarse NeRF, coarse NeuS, geometry refinement, texture refinement, validation/test/export launch modes, config overrides, or checkpoint handoffs.

## Read first

- Read [references/staged-workflow.md](references/staged-workflow.md) for the four-stage command chain, required overrides, inputs/outputs, and pre/post-run checks.
- Read [references/configs-and-artifacts.md](references/configs-and-artifacts.md) for distilled config facts, registry names, model/data artifacts, and memory-resolution knobs.
- Read [references/troubleshooting.md](references/troubleshooting.md) for stage startup, config, checkpoint, CUDA, model, and OOM failures.
- Use [scripts/build_dreamcraft3d_commands.py](scripts/build_dreamcraft3d_commands.py) to generate shell-quoted commands without launching training.

## When to use this sub-skill

Use it for requests like:

- "Give me the DreamCraft3D command sequence for my image and prompt."
- "Which checkpoint from stage 1 feeds the geometry stage?"
- "What overrides are required for `configs/dreamcraft3d-texture.yaml`?"
- "Reduce memory usage for NeuS or DMTet stages."
- "Explain why `???` appears in a config error."

## Pipeline protocol

1. Confirm the input image has the sidecars required by the selected config. Route to `image-preparation` if `_rgba`, `_depth`, or `_normal` files are missing.
2. Build commands instead of improvising them. The main `launch.py` CLI requires `--config`, one mode flag, and optional `--gpu`; remaining settings are OmegaConf overrides.
3. Run stages in order unless the user supplies an existing checkpoint:
   - coarse NeRF: creates a first geometry/radiance checkpoint,
   - coarse NeuS: refines from the NeRF checkpoint with `system.weights`,
   - geometry: converts from the NeuS checkpoint with `system.geometry_convert_from`,
   - texture: converts from the geometry checkpoint with `system.geometry_convert_from`.
4. Treat full execution as CUDA/model/checkpoint dependent. Do not call a static config parse or command build a successful training run.

## Safe command generation

```bash
python <skill-dir>/sub-skills/generation-pipeline/scripts/build_dreamcraft3d_commands.py \
  --prompt "a brightly colored mushroom growing on a log" \
  --image-path load/images/mushroom_log_rgba.png --gpu 0
```

Add `--json` when another tool needs structured commands. Use checkpoint override options when resuming from known artifacts.

## Route elsewhere

- Image preprocessing and sidecar validation: `image-preparation`.
- Optional Zero123++ multiview and DreamBooth/LoRA texture boosting: `bootstrapped-texture`.
- Mesh export details, output summaries, metrics, and videos: `export-and-evaluation`.
- Docker, Gradio, and broad installation/backend triage: `interfaces-and-monitoring`.
