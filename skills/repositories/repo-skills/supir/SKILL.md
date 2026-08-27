---
name: supir
description: "Operate SUPIR for CUDA photo restoration, upscaling,
  caption-assisted enhancement, tiled restoration, face restoration, and safe
  checkpoint/configuration troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# SUPIR Repo Skill

Use this skill when a task is about SUPIR, SupPixel/SUPIR photo restoration,
photo-realistic image enhancement, image upscaling, caption-assisted diffusion
restoration, SUPIR checkpoints, `SUPIR`/`sgm`/`llava` imports, or the repo's
batch and Gradio-style workflows.

SUPIR is a CUDA-first research preview. Do not treat it as a CPU package. Its
public workflows load large SDXL, SUPIR, CLIP, and LLaVA checkpoints and can be
expensive. Prefer preflight and dry-run checks before model loading.

## First checks

1. Read [references/checkpoints-and-environment.md](references/checkpoints-and-environment.md) before running anything that loads a model. It lists required checkpoint variables, config files, backend assumptions, and optional UI/face dependencies.
2. Use [scripts/check_supir_assets.py](scripts/check_supir_assets.py) to inspect a config and validate candidate checkpoint paths without loading weights.
3. If imports or CUDA fail, read [references/troubleshooting.md](references/troubleshooting.md) before changing package versions.
4. For YAML variants and shared parameters, read [references/configuration-reference.md](references/configuration-reference.md).

## Route by task

| User task or signal | Read next |
| --- | --- |
| Programmatic use of `SUPIR.util`, `create_SUPIR_model`, `SUPIRModel.batchify_sample`, image/tensor conversion, model config loading, LLaVA caption agent, or API signatures | [sub-skills/python-api-and-config/SKILL.md](sub-skills/python-api-and-config/SKILL.md) |
| Folder/batch restoration, `--img_dir`, `--save_dir`, `SUPIR_sign`, quality/fidelity flags, `--no_llava`, output naming, or a `test.py`-style run | [sub-skills/batch-restoration/SKILL.md](sub-skills/batch-restoration/SKILL.md) |
| Browser UI, Gradio launch, `--use_image_slider`, `--log_history`, tiled/local prompt mode, large-image memory, face restoration, `face_resolution`, or demo port binding | [sub-skills/interactive-demos/SKILL.md](sub-skills/interactive-demos/SKILL.md) |
| Checkpoint/environment errors shared by all workflows | [references/troubleshooting.md](references/troubleshooting.md) and [references/checkpoints-and-environment.md](references/checkpoints-and-environment.md) |

## Operating model

- SUPIR normally uses one CUDA device for restoration and a second CUDA device
  for LLaVA captioning when two GPUs are visible. With one GPU both model
  families share the same device. With no CUDA device the repo scripts abort.
- `Q` and `F` select different SUPIR restoration checkpoints. `Q` is the
  default high-quality/general checkpoint; `F` favors fidelity under light
  degradation.
- LLaVA is optional for several workflows. When captioning is unavailable, use
  manual prompts or `--no_llava`/local-prompt routes.
- The UI/demo stack is optional unless the user wants browser interaction. The
  core API/batch environment can be valid without Gradio installed.
- Respect the upstream non-commercial-use declaration when planning usage or
  deployment.

## Self-contained assets in this skill

- [scripts/check_supir_assets.py](scripts/check_supir_assets.py): safe config and checkpoint validator.
- [sub-skills/python-api-and-config/scripts/supir_api_probe.py](sub-skills/python-api-and-config/scripts/supir_api_probe.py): safe import/signature probe.
- [sub-skills/batch-restoration/scripts/supir_batch_restore.py](sub-skills/batch-restoration/scripts/supir_batch_restore.py): adapted batch-restoration wrapper with `--dry-run` support.
- [sub-skills/interactive-demos/scripts/supir_demo_preflight.py](sub-skills/interactive-demos/scripts/supir_demo_preflight.py): safe launcher preflight for standard, tiled, and face demo modes.

## Avoid these mistakes

- Do not load checkpoints just to inspect CLI flags or signatures; use the
  bundled probes first.
- Do not assume a CPU import check verifies SUPIR restoration. CUDA is required
  for truthful end-to-end validation.
- Do not paste private absolute checkpoint paths into prompts, reports, or
  generated configs. Use environment variables or user-provided public paths.
- Do not route generic Stable Diffusion image generation or unrelated LLaVA
  serving tasks here unless SUPIR source APIs, configs, or workflows are named.

## Provenance and routing metadata

- Source snapshot and evidence paths: [references/repo-provenance.md](references/repo-provenance.md).
- Router metadata: [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
