---
name: text-to-image-generation
description: "Write and debug Python min-dalle text-to-image generation calls,
  streams, tensor/PIL outputs, sampling controls, seamless tiling, seeds,
  devices, dtypes, and reuse choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Text-to-Image Generation

Use this sub-skill when a future agent needs to write, adapt, or debug Python `MinDalle` text-to-image calls: model construction, single-image grids, per-image tensor batches, progressive streams, sampling parameters, seamless tiling, reproducible seeds, `is_mega`, `is_reusable`, `device`, and `dtype` choices.

Start here:

- Use [references/api-reference.md](references/api-reference.md) for verified `MinDalle` signatures, output types, shapes, and parameter semantics.
- Use [references/generation-workflows.md](references/generation-workflows.md) for reusable Python recipes and safe dry-run/run command patterns.
- Use [references/troubleshooting.md](references/troubleshooting.md) for generation-specific failures and recovery steps.
- Use [scripts/generation_request_template.py](scripts/generation_request_template.py) as a safe standalone request template. It defaults to dry run and only constructs/downloads models when `--run` is supplied.

Operating rules:

1. Prefer keyword arguments for all generation calls. In particular, `generate_images()` and `generate_images_stream()` need `grid_size` in `kwargs` because the implementation reshapes output batches from `kwargs["grid_size"]`.
2. Choose output API by desired form: `generate_image()`/`generate_image_stream()` for PIL grid images; `generate_images()`/`generate_images_stream()` for tensor batches of individual 256×256 images; `generate_raw_image_stream()` for raw grid tensors.
3. Treat `MinDalle(...)` construction as potentially expensive: tokenizer assets may be requested immediately, and full encoder/decoder/detokenizer weights load during construction when `is_reusable=True`. Route cache/download/storage and detailed dtype memory planning to [../model-assets-and-runtime/SKILL.md](../model-assets-and-runtime/SKILL.md).
4. Keep this sub-skill scoped to the Python API. Route command-line `image_from_text.py`, Tkinter UI, Colab notebook UX, Replicate, Spaces, or public deployment interface tasks to [../deployment-and-interfaces/SKILL.md](../deployment-and-interfaces/SKILL.md).
5. Do not ask future agents to inspect the original repository files for these API facts; use the distilled references here as the runtime operating context.
