---
name: interactive-demos
description: "Launch, preflight, and troubleshoot SUPIR interactive demo modes:
  standard Gradio UI, tiled/local-prompt restoration, and face restoration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Interactive Demos

Use this sub-skill when the user asks for a browser UI, Gradio launch,
`--use_image_slider`, `--log_history`, tiled/local prompt mode, large-image
memory handling, face restoration, face crop/paste behavior, or demo port
troubleshooting.

For non-interactive folder processing, route to
[../batch-restoration/SKILL.md](../batch-restoration/SKILL.md). For low-level
API questions, route to
[../python-api-and-config/SKILL.md](../python-api-and-config/SKILL.md).

## Read these bundled files

- [references/demo-workflows.md](references/demo-workflows.md) for mode
  comparison, launch options, UI control behavior, and demo-specific
  troubleshooting.
- [scripts/supir_demo_preflight.py](scripts/supir_demo_preflight.py) for a safe
  preflight that prints a launch command, validates mode/config choices, and
  optionally checks imports without starting a server.
- [../../references/checkpoints-and-environment.md](../../references/checkpoints-and-environment.md)
  for checkpoint and optional UI dependency planning.
- [../../references/troubleshooting.md](../../references/troubleshooting.md)
  for shared CUDA, dependency, and checkpoint failures.

## Demo modes

| Mode | Source workflow distilled | Best for | Special risks |
| --- | --- | --- | --- |
| `main` | Standard stage1/LLaVA/stage2 Gradio UI | Manual prompt editing, quality/fidelity presets, feedback/history logging | Gradio optional dependency stack, port binding, large model load at startup |
| `tiled` | Tiled/local-prompt UI variant | Large images, local prompt lists, memory-sensitive runs | Tile size choices, slower VAE hooks, prompt list batch-size restriction |
| `face` | Face detection/crop/restore/paste-back variant | Portrait/face-focused restoration with optional background restore | facexlib model assets, no-face/multiple-face handling, crop size alignment |

## Safe launch flow

1. Validate core imports and CUDA with the API sub-skill.
2. Validate checkpoint paths and config variant.
3. Run the demo preflight:

```bash
python sub-skills/interactive-demos/scripts/supir_demo_preflight.py --mode main --port 6688
python sub-skills/interactive-demos/scripts/supir_demo_preflight.py --mode tiled --local-prompt --use-tile-vae
python sub-skills/interactive-demos/scripts/supir_demo_preflight.py --mode face --face-resolution 1024
```

4. Install optional UI dependencies only when the user really wants to launch a
   browser UI.
5. Start the demo in a user-approved working directory if `--log_history` is
   enabled, because history writes to a relative `history/` tree.

## Common decisions

- Use `--no_llava` when captioning weights are unavailable; ask the user for a
  prompt rather than silently loading remote LLaVA weights.
- Use tiled mode when the requested image size or GPU memory makes the standard
  VAE path risky.
- Use face mode only when the task genuinely needs face crop restoration and
  facexlib assets are available.
- Use a private/loopback IP such as `127.0.0.1` unless the user approves binding
  to a public interface.

## Guardrails

- Demo scripts load models at startup; do not import or launch them just to
  inspect flags.
- Gradio dependency resolution can conflict with the core LLaVA/Transformers
  stack. Separate UI environments are acceptable when needed.
- Do not expose a demo server on `0.0.0.0` without explicit user approval.
- Do not treat feedback/history logs as anonymous; the source UI can collect
  prompt and output metadata when logging is enabled.
