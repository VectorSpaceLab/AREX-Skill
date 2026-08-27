---
name: magi-1
description: "Operate MAGI-1 autoregressive video generation inference, ComfyUI
  nodes, configs, and prompt enhancement assets."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# MAGI-1 repo skill

Use this skill when a task is about MAGI-1, the SandAI autoregressive video generation repository, including source-code inference, model/config selection, CUDA/runtime setup, ComfyUI custom nodes, or the bundled Dify prompt-enhancement workflow.

MAGI-1 is not a lightweight CPU library. Real generation needs CUDA, the MAGI DiT weights, T5 weights, VAE weights, special-token assets, and ffmpeg. This skill provides self-contained operating guidance and safe preflight helpers; it does not include model weights.

## Route by task

| User task | Read |
| --- | --- |
| Build or debug `t2v`, `i2v`, or `v2v` source-code commands | [sub-skills/inference/SKILL.md](sub-skills/inference/SKILL.md) |
| Edit or validate MAGI JSON configs, checkpoint paths, process counts, or CFG/distill/fp8 settings | [sub-skills/inference/SKILL.md](sub-skills/inference/SKILL.md) and [sub-skills/inference/references/configuration.md](sub-skills/inference/references/configuration.md) |
| Use the Python `MagiPipeline` API | [sub-skills/inference/references/cli-and-api.md](sub-skills/inference/references/cli-and-api.md) |
| Install, recognize, or operate the MAGI-1 ComfyUI custom node | [sub-skills/comfyui/SKILL.md](sub-skills/comfyui/SKILL.md) |
| Import or adapt MAGI ComfyUI workflow JSONs | [sub-skills/comfyui/references/comfyui-nodes-and-workflows.md](sub-skills/comfyui/references/comfyui-nodes-and-workflows.md) |
| Prepare weights, runtime dependencies, or safe environment checks | [references/installation-and-assets.md](references/installation-and-assets.md) and [scripts/magi_runtime_preflight.py](scripts/magi_runtime_preflight.py) |
| Understand model families and hardware expectations | [references/model-and-config-overview.md](references/model-and-config-overview.md) |
| Use the prompt enhancement DSL outside MAGI generation | [references/dify-prompt-enhancement.md](references/dify-prompt-enhancement.md) |
| Diagnose install/import, asset, CUDA, ffmpeg, or cross-workflow issues | [references/troubleshooting.md](references/troubleshooting.md) plus the nearest sub-skill troubleshooting reference |

## Common operating path

1. Choose the user-facing surface:
   - Source CLI/API inference: use the `inference` sub-skill.
   - ComfyUI node graph: use the `comfyui` sub-skill.
   - Prompt rewriting in Dify: use the Dify reference.
2. Choose a model family from [references/model-and-config-overview.md](references/model-and-config-overview.md). Prefer 4.5B variants for single-GPU use; 24B examples are multi-GPU configurations.
3. Download or locate local MAGI DiT, T5, and VAE weights. Edit a copied JSON config so `load`, `t5_pretrained`, and `vae_pretrained` point to local paths.
4. Run [scripts/magi_runtime_preflight.py](scripts/magi_runtime_preflight.py) in the runtime Python to check CUDA, attention packages, ffmpeg, and optional source assets.
5. For source CLI/API, run [sub-skills/inference/scripts/magi_config_check.py](sub-skills/inference/scripts/magi_config_check.py) before generation and [sub-skills/inference/scripts/magi_command_builder.py](sub-skills/inference/scripts/magi_command_builder.py) to print a command.
6. For ComfyUI, import one of the bundled workflow JSONs from [sub-skills/comfyui/references/workflows/](sub-skills/comfyui/references/workflows/) and reassign every placeholder path inside the UI before queueing.
7. If anything fails, read [references/troubleshooting.md](references/troubleshooting.md) first, then the workflow-specific troubleshooting page.

## Strong constraints and safety notes

- Do not present a config parse, helper output, or import check as a successful video generation. A real MAGI smoke test must load weights and write a playable MP4.
- Do not tell users to run original repository examples from an absent checkout. Use this skill's bundled helpers and references to reconstruct safe commands and checks.
- Do not claim CPU-only generation support. CUDA is required by MAGI source distributed initialization and model code paths.
- Match `engine_config.pp_size * engine_config.cp_size` to the launched process count. The bundled inference config checker validates this preflight.
- Treat model architecture fields as checkpoint-coupled. For most tasks, copy a release-family config and edit paths, seed, output dimensions, frame count, steps, FPS, and parallel sizes only when launch topology changes.
- The ComfyUI node path is single-process/single-GPU by default because `MagiProcess` sets its own distributed and CUDA visibility environment variables.
- Large model downloads, full generation, and ComfyUI host operation may be expensive or environment-specific. Ask for user approval before long downloads or long generation runs.

## Bundled helpers

- [scripts/magi_runtime_preflight.py](scripts/magi_runtime_preflight.py): checks Python version, key dependency imports, CUDA visibility, optional tiny CUDA tensor execution, ffmpeg availability, and optional MAGI source asset paths without loading model weights.
- [sub-skills/inference/scripts/magi_config_check.py](sub-skills/inference/scripts/magi_config_check.py): validates MAGI JSON config schema, CFG/distill/fp8 rules, process-count alignment, and optional checkpoint paths.
- [sub-skills/inference/scripts/magi_command_builder.py](sub-skills/inference/scripts/magi_command_builder.py): prints a source-code inference command and recommended environment variables; it does not execute generation.
- [sub-skills/comfyui/scripts/inspect_workflow_nodes.py](sub-skills/comfyui/scripts/inspect_workflow_nodes.py): inspects ComfyUI workflow JSONs offline and lists MAGI nodes plus placeholder fields.

## Provenance and routing metadata

- Source snapshot and evidence paths are recorded in [references/repo-provenance.md](references/repo-provenance.md).
- Managed router metadata for repo-skill import is recorded in [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
