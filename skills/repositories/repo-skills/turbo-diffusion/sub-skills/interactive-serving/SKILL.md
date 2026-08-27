---
name: interactive-serving
description: "Operate TurboDiffusion's interactive T2V/I2V terminal server with
  safe launch validation, TUI commands, and runtime parameter handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TurboDiffusion interactive serving

Use this sub-skill when the task is to launch or troubleshoot TurboDiffusion's interactive terminal server for repeated text-to-video (T2V) or image-to-video (I2V) generations while keeping loaded model objects alive across prompts.

## Route here for

- Choosing an installed CLI vs Python-module TUI launch command.
- Validating T2V `--dit_path` vs I2V `--high_noise_model_path` and `--low_noise_model_path` before opening the TUI.
- Explaining the TUI prompt flow, slash commands, output path prompts, and I2V image path prompts.
- Adjusting runtime parameters with `/set` without restarting the server.
- Diagnosing source-layout import errors, missing mode-specific model paths, invalid resolution/aspect ratio selections, `/set` validation errors, and interactive cancellation.

## Route elsewhere

- One-shot, non-interactive T2V/I2V scripts, prompt files, and direct `--save_path` generation: use the sibling `video-inference` sub-skill.
- CUDA extension builds, `turbo_diffusion_ops`, SageSLA/SpargeAttn installation, quantized-linear backend failures, or FastNorm/custom-op checks: use the sibling `acceleration-backends` sub-skill.
- Checkpoint conversion, training, model merging, or quantized checkpoint export: use the sibling `training-and-checkpoints` sub-skill.

## Runtime files

- [TUI server guide](references/tui-server.md): launch flow, model residency behavior, slash commands, prompt/image/output handling, and runtime-adjustable parameters.
- [CLI reference](references/cli-reference.md): public launch methods, argument tables, mode-specific requirements, defaults, and resolution/aspect-ratio validation.
- [Troubleshooting](references/troubleshooting.md): failure matrix for import quirks, missing model paths, invalid CLI values, `/set` errors, cancellation, and backend-routed problems.
- [Command renderer](scripts/build_serve_command.py): safe dry-run helper that renders, but never executes, a T2V or I2V TUI launch command.

## Quick operating pattern

1. Decide whether the user needs the installed `turbodiffusion-serve` entry point or `python -m turbodiffusion.serve`.
2. Use [the command renderer](scripts/build_serve_command.py) or the tables in [CLI reference](references/cli-reference.md) to build a mode-correct launch.
3. For source-layout installs, prepend a public `PYTHONPATH` entry that exposes TurboDiffusion's top-level `imaginaire`, `rcm`, and inference helper modules; a common source checkout uses `PYTHONPATH=turbodiffusion`.
4. Once the TUI starts, keep it running for multiple prompts so VAE/model objects remain loaded instead of paying startup cost per generation.
5. Use [Troubleshooting](references/troubleshooting.md) before changing backend packages or rerouting to another sub-skill.
