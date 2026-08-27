---
name: backend-and-api
description: "Reason about Dream Textures backend API contracts,
  DiffusersBackend routing, generator subprocess behavior, schedulers,
  model/task compatibility, and custom backend diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Backend and API

Use this sub-skill when a task is about Dream Textures' backend extension surface or local Diffusers backend internals rather than a user-facing prompt recipe.

## Route Here

- Implement or update a custom backend, including `Backend.generate(arguments, step_callback, callback)` and `GenerationResult` callbacks.
- Inspect or reason about `GenerationArguments`, `Task` dataclasses, `Prompt`, `Model`, `ControlNet`, `GenerationResult`, `SeamlessAxes`, or `StepPreviewMode`.
- Diagnose `DiffusersBackend` model/task validation, scheduler enum errors, device selection, model cache invalidation, checkpoint conversion/loading, SDXL refiner behavior, ControlNet routing, or optimization flags.
- Understand the `Generator` actor/Future callback lifecycle without running Blender UI, model downloads, or original repository tests.
- Handle source-level symptoms such as missing `bpy` outside Blender, stale community backend signatures, cancellation that never calls back, or optional backend dependency import failures.

## Start With

- [API Reference](references/api-reference.md) for verified public dataclass, enum, and `Backend` method signatures.
- [Diffusers Backend](references/diffusers-backend.md) for task routing, model loading, scheduler values, device order, optimizations, and compatibility checks.
- [Custom Backends](references/custom-backends.md) when writing or porting a backend.
- [Troubleshooting](references/troubleshooting.md) for symptom-oriented backend/API diagnosis.
- [`scripts/inspect_public_api.py`](scripts/inspect_public_api.py) for safe signature/enum inspection in a minimal Python environment with NumPy and either an installed Dream Textures package or a supplied add-on source directory.

## Boundaries

- End-user prompt, inpaint/outpaint, ControlNet-from-image, history, seamless texture, and upscaling recipes belong in the sibling `generation-workflows` sub-skill.
- Installation, dependency variants, model acquisition, Hugging Face tokens, DreamStudio keys, and checkpoint import UI guidance belong in `setup-and-models`.
- Texture projection, scene nodes, annotation maps, render passes, compositor sockets, and Cycles integration belong in `scene-integration`.
- Do not treat full Stable Diffusion inference, Blender UI execution, or original repository tests as required checks for this sub-skill; use source-backed reasoning and safe helper inspection.

## Safe Inspection Pattern

```bash
python scripts/inspect_public_api.py --help
python scripts/inspect_public_api.py --addon-dir /path/to/dream_textures --json
```

The helper sets backend/actor inspection stubs, avoids Blender UI imports, and does not download models. If the user's add-on directory is already installed/importable as `dream_textures`, `--addon-dir` can be omitted. A direct source directory with another basename is inspected via `sys.path` insertion using that basename only; no symlink, copy, or source mutation is performed.
