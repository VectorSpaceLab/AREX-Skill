---
name: export-and-evaluation
description: "Export DreamCraft3D meshes, inspect output directories, and plan
  optional metrics or progress videos."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Export and Evaluation

Use this sub-skill when a task is about exporting a trained DreamCraft3D result, finding checkpoints/configs, summarizing `outputs/` or `outputs-gradio/`, diagnosing mesh-export failures, or planning optional CLIP/LPIPS/CX/PSNR metrics and progress videos.

## Read first

- Read [references/metrics-and-export.md](references/metrics-and-export.md) for mesh export commands, exporter options, metric utilities, and video helper guidance.
- Read [references/output-layout.md](references/output-layout.md) for trial directory structure, checkpoint handoffs, and where validation/test/export assets appear.
- Read [references/troubleshooting.md](references/troubleshooting.md) when export fails because of missing checkpoints, parsed configs, nvdiffrast context, texture maps, or metrics dependencies.
- Use [scripts/summarize_outputs.py](scripts/summarize_outputs.py) to inspect an output trial directory without importing torch or running export.

## When to use this sub-skill

Use it for requests like:

- "Export an OBJ from my DreamCraft3D checkpoint."
- "Find the `last.ckpt` and `parsed.yaml` for a run."
- "Why does mesh export fail in a headless Docker container?"
- "Summarize what artifacts exist under this output directory."
- "How do the optional metrics scripts expect inputs?"

## Export protocol

1. Confirm the texture or geometry trial has both `configs/parsed.yaml` and a compatible checkpoint such as `ckpts/last.ckpt`.
2. Build the export command using `launch.py --export`, `resume=<checkpoint>`, and `system.exporter_type=mesh-exporter`.
3. Expect actual export to require CUDA, the active DreamCraft3D environment, nvdiffrast, xatlas, and any checkpoint-specific model components.
4. After export, inspect the generated export directory for OBJ/MTL/texture artifacts.

## Safe output summary

```bash
python <skill-dir>/sub-skills/export-and-evaluation/scripts/summarize_outputs.py \
  --trial-dir outputs/dreamcraft3d-texture/<prompt-tag>@LAST --require-checkpoint --require-parsed-config
```

Use `--json` for structured output and `--require-export` when checking an already exported trial.

## Route elsewhere

- Four-stage training and checkpoint chaining before export: `generation-pipeline`.
- Image input and sidecars: `image-preparation`.
- LoRA/Zero123++ texture boosting: `bootstrapped-texture`.
- Gradio live progress and Docker setup: `interfaces-and-monitoring`.
