---
name: python-api
description: "Programmatic Deep Daze API use for Imagine and DeepDaze
  construction, prompt/image/encoding workflows, progress saving, optimizers,
  and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# python-api

Use this sub-skill when a task needs to call Deep Daze from Python rather than assemble shell commands. It covers safe `Imagine` and `DeepDaze` construction, prompt/image/custom-encoding choices, story mode, start-image priming, output path helpers, progress saving, optimizers, reproducibility knobs, and API-level failure modes.

## Route first

- For command-line invocation, flags, quoting, overwrite prompts, and shell workflow construction, route to [`../cli-workflows/SKILL.md`](../cli-workflows/SKILL.md).
- For installation, CLIP model cache/download/network diagnosis, CUDA/CPU availability, package compatibility, and backend memory diagnosis, route to [`../runtime-and-models/SKILL.md`](../runtime-and-models/SKILL.md).
- Stay here for Python call structure, constructor arguments, API defaults, helper methods, and code-level troubleshooting after the environment is usable.

## Operating sequence

1. Decide the objective input: exactly one of text-only, image-only, combined text+image, or a precomputed CLIP encoding unless deliberately replacing the target later with `set_clip_encoding`.
2. Pick conservative constructor settings before instantiating `Imagine`; construction loads CLIP and may perform model retrieval through the runtime cache.
3. Set `open_folder=False` for noninteractive agents and control the current working directory because images, progress frames, story transitions, GIFs, and videos are written relative to it.
4. Use exact optimizer names: `AdamP`, `Adam`, or `DiffGrad`.
5. Run `scripts/probe_api_surface.py --verify` when a lightweight API check is needed without constructing `Imagine` or downloading CLIP weights.
6. Use the references for details:
   - [`references/api-reference.md`](references/api-reference.md) for signatures, defaults, helper behavior, and method semantics.
   - [`references/workflow-recipes.md`](references/workflow-recipes.md) for Python recipes including low/high VRAM presets.
   - [`references/troubleshooting.md`](references/troubleshooting.md) for constructor, prompt, image, story, optimizer, saving, determinism, and memory pitfalls.

## Minimal Python pattern

```python
from deep_daze import Imagine

imagine = Imagine(
    text="a house in the forest",
    epochs=1,
    iterations=100,
    save_every=25,
    save_progress=True,
    open_folder=False,
)
imagine()
```

## Safety notes

- `Imagine(...)` is not a cheap metadata operation: instantiate only when ready for CLIP loading and potential cache use.
- Regular text prompts must fit CLIP tokenization; use story mode for longer prose but still validate each story segment.
- `DeepDaze` is the lower-level SIREN module and requires an already loaded CLIP perceptor, normalization transform, input resolution, total-batch count, and batch settings.
