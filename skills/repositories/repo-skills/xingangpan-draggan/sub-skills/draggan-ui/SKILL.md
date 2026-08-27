---
name: draggan-ui
description: "Guides DragGAN desktop and Gradio point-based image manipulation,
  checkpoint selection, masks, latent-space controls, and UI troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DragGAN UI

Use this route for desktop visualizer or Gradio tasks: launch the app, load a StyleGAN checkpoint, choose a seed, place source/target point pairs, constrain edits with masks, or debug UI/model-loading failures.

## Before launch

1. Run the root `scripts/check_environment.py` with the local checkout and confirm CUDA for real drag optimization.
2. Run the root `scripts/check_model_assets.py --checkpoint-dir <dir>`.
3. Use [references/ui-workflows.md](references/ui-workflows.md) for the control model and launch decisions.
4. Use [references/troubleshooting.md](references/troubleshooting.md) for GUI, checkpoint, CUDA, and import errors.

The bundled launch helpers are dry-run by default:

```bash
python sub-skills/draggan-ui/scripts/launch_draggan_gui.py \
  --repo-root /path/to/DragGAN --checkpoint-dir checkpoints
python sub-skills/draggan-ui/scripts/launch_gradio_demo.py \
  --repo-root /path/to/DragGAN --cache-dir checkpoints --listen
```

Pass `--execute` only after the printed command and preflight output are correct. The desktop helper scans existing `.pkl` files and supports `--pkl`, `--capture-dir`, and `--browse-dir`. The Gradio helper requires at least one checkpoint and supports `--cache-dir`, `--listen`, and `--share`.

## Editing model

- A point pair consists of a source point and a target point; incomplete pairs should be reset before starting.
- The flexible-area mask allows optimization in selected regions; the fixed-area mode protects selected regions. Reset or show the mask before diagnosing a stalled drag.
- `w` optimization is faster/more global; `w+` is slower but usually gives finer local control.
- Step size/learning rate, motion lambda, feature index, `r1`, and `r2` affect stability and locality. Change one parameter at a time.
- Loading a new checkpoint or seed resets image, point, and mask state.

## Related routes

- Batch generation, interpolation, style mixing, or legacy pickle conversion: [../stylegan-generation/SKILL.md](../stylegan-generation/SKILL.md).
- StyleGAN-Human alignment, PTI, attribute editing, and InsetGAN: [../stylegan-human-manipulation/SKILL.md](../stylegan-human-manipulation/SKILL.md).
- Training a StyleGAN-Human model: [../stylegan-training/SKILL.md](../stylegan-training/SKILL.md).

## Bundled files

- [references/ui-workflows.md](references/ui-workflows.md) contains the interaction and launch recipes.
- [references/troubleshooting.md](references/troubleshooting.md) contains UI-specific recovery steps.
- [scripts/launch_draggan_gui.py](scripts/launch_draggan_gui.py) wraps the desktop entry point with checkpoint preflight.
- [scripts/launch_gradio_demo.py](scripts/launch_gradio_demo.py) wraps the Gradio entry point with cache-dir preflight.
