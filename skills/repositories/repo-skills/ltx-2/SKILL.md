---
name: ltx-2
description: "Routes LTX-2 audio-video generation, training, data preparation,
  core APIs, and performance-backend tasks across the ltx-core, ltx-pipelines,
  ltx-trainer, and ltx-kernels packages."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# LTX-2 repo skill

Use this repo skill when a task involves Lightricks **LTX-2** / **LTX-2.3** / **LTX-2.5** audio-video generation, LTX training/fine-tuning, package APIs, model asset layout, CUDA/backend troubleshooting, or dataset preprocessing for LTX Trainer.

This skill is a self-contained operating guide for the LTX-2 package family. It distills the repository evidence into bundled references and helpers; do not rely on original repository docs, examples, or scripts during normal use.

## Setup and checks

If you are working from a source checkout, install the packages with the repository's workspace sync and then run the environment checker:

```bash
uv sync
python path/to/ltx-2/scripts/check_ltx2_environment.py --json
```

If your task needs optional acceleration, add only the backend that the selected route requires: read `performance-backends` before installing `natten`, `ltx-kernels`, or other accelerator-specific extras.

Read [references/package-map.md](references/package-map.md) for the monorepo package roles and [references/model-assets.md](references/model-assets.md) for LTX-2.5 split assets versus LTX-2.3 monolith assets. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install, checkpoint, Gemma, and CUDA problems.

## Routes

| User request | Read |
| --- | --- |
| Choose a generation pipeline, build a CLI/Python inference command, use LTX-2.5 split checkpoints, use image/video/audio conditioning, retake, HDR/EXR, Dub-It, DFR, or text-to-audio. | [sub-skills/inference-pipelines/SKILL.md](sub-skills/inference-pipelines/SKILL.md) |
| Validate a dataset manifest, plan scene splitting/captioning/preprocessing, choose resolution buckets, inspect `.precomputed/`, prepare references or masks. | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) |
| Choose a training mode, patch trainer YAML, validate a config, plan launch/monitor/resume, troubleshoot LoRA/full fine-tuning. | [sub-skills/training-workflows/SKILL.md](sub-skills/training-workflows/SKILL.md) |
| Write custom Python code using `ltx_core` model builders, schedulers, guiders, conditioning items, ModelPaths, LoRA/SDOps, quantization policies, or tensor shape contracts. | [sub-skills/core-components/SKILL.md](sub-skills/core-components/SKILL.md) |
| Choose CUDA/FP8/NVFP4/offload/compile/DiffVAE/NATTEN/ltx-kernels/multi-GPU performance paths or diagnose backend readiness. | [sub-skills/performance-backends/SKILL.md](sub-skills/performance-backends/SKILL.md) |

## Common operating rules

- LTX model paths are local files or directories. Do not pass Hugging Face URLs where the code expects a filesystem path.
- LTX-2.5 split layout uses one file per component: transformer, packed text encoder, video VAE, audio VAE, optional upsamplers, optional duration head, and optional LoRAs.
- LTX-2.3/legacy monolith layout uses one large `.safetensors` plus a matching Gemma directory; LTX-2.5 components are not interchangeable with LTX-2.3 components.
- Video frame counts generally follow the VAE temporal grid (`F % T == 1`; default `T=8`) and width/height generally must be divisible by the VAE spatial factor (default `32`).
- Real generation, preprocessing, training, kernel builds, model downloads, and external uploads are expensive or stateful. Build and validate commands first, then ask for approval before running them.
- For accelerator or optional backend claims, distinguish import/parser checks from actual CUDA/kernel/runtime checks. A CPU import is not proof that generation/training will run.

## Maintenance and freshness

Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a current checkout. If the source commit, package metadata, public APIs, or docs changed materially, run `refresh-repo-skill` rather than editing this skill ad hoc.

Router import metadata is in [references/repo-routing-metadata.json](references/repo-routing-metadata.json). This creation run was requested with **not import**, so the runtime tree is prepared for verification but not installed into the managed repo-skill library by this workflow.
