# Troubleshooting: Python Generation

Use this guide for failures in Python `MinDalle` construction and generation calls. For cache location, download policy, package/runtime preparation, GPU memory budgeting, or dtype benchmark planning, route to `../model-assets-and-runtime/SKILL.md`. For CLI, Tkinter, Colab, or Replicate interface issues, route to `../deployment-and-interfaces/SKILL.md`.

## Constructor downloads or takes longer than expected

Symptoms:

- `MinDalle(...)` prints tokenizer/model initialization messages and appears to download files.
- Construction succeeds on one machine but hangs or fails in an offline environment.
- Dry-run planning seemed fast, but `--run` starts network/model activity.

Likely causes:

- The constructor always initializes the tokenizer and can request tokenizer assets if absent.
- With `is_reusable=True`, the constructor also initializes/downloads encoder, decoder, and detokenizer weights.
- With `is_reusable=False`, full weights are delayed until generation, not eliminated.

Recovery:

1. Use `scripts/generation_request_template.py` without `--run` to print the planned call without model construction.
2. Confirm the model cache exists or network downloads are allowed before adding `--run`.
3. For a one-shot lower-residency run, try `--non-reusable`; for repeated prompts, use `--reusable` after memory is planned.
4. Route unresolved cache/download/storage issues to the model-assets/runtime sub-skill.

## Import errors

Symptoms:

- `ImportError: No module named 'min_dalle'`.
- `ImportError` for dependencies such as `torch`, `PIL`, `requests`, or `emoji`.

Recovery:

1. Run the dry-run script first; it should not import `MinDalle`.
2. Use `--run` only in an environment where `from min_dalle import MinDalle` works.
3. Install the package with its runtime dependencies, then re-run a small `--grid-size 1 --no-mega --device cpu --dtype float32` smoke request if downloads are allowed.
4. If dependency installation or backend selection is the hard part, route to model-assets/runtime preparation.

## Invalid or unavailable device

Symptoms:

- `CUDA requested but torch.cuda.is_available() is False`.
- `Invalid device string` or device transfer failures.
- A run silently falls back to CPU and becomes very slow.

Recovery:

1. Use `--device auto` or pass `device=None` in Python to let `MinDalle` choose CUDA when available, otherwise CPU.
2. Use `--device cpu` for compatibility tests and `--device cuda` or `--device cuda:0` only when CUDA PyTorch is installed and a GPU is visible.
3. The verified API contract covers `cpu` and `cuda`; avoid unverified device types for production recipes unless a separate environment check proves them.

## Invalid dtype or dtype/device mismatch

Symptoms:

- `Invalid dtype` from the request template.
- Runtime errors or poor performance after choosing `float16`/`bfloat16` on CPU.
- CUDA autocast warnings or unsupported precision failures.

Recovery:

1. Use `--dtype float32` first, especially on CPU.
2. Use `--dtype float16` to reduce CUDA memory when the GPU supports it.
3. Use `--dtype bfloat16` only on capable CUDA hardware; the README specifically calls out Ampere-class GPUs.
4. If the task is primarily memory planning or precision benchmarking, route to model-assets/runtime.

## GPU out-of-memory, process killed, or severe slowness

Symptoms:

- CUDA OOM, process killed by the OS, or generation takes much longer than expected.
- Failures appear only at larger `grid_size` values.

Likely causes:

- `grid_size` controls image count quadratically: image count is `grid_size ** 2`.
- The mega model is much larger than mini.
- `is_reusable=True` keeps all major modules resident.
- Progressive outputs add repeated detokenization overhead.

Recovery:

1. Reduce to `--grid-size 1` and `--no-mega` for a smoke test.
2. On CUDA, try `--dtype float16`; on CPU, stay with `float32`.
3. For one-shot generation, try `--non-reusable` to avoid keeping all modules resident between phases.
4. Disable `--progressive-outputs` unless intermediate frames are required.
5. Escalate detailed GPU/cache planning to model-assets/runtime.

## `top_k` or temperature misuse

Symptoms:

- Index errors near token sampling.
- Degenerate, noisy, or overly repetitive outputs.
- Division-by-zero or invalid floating-point behavior.

Recovery:

- Keep `top_k` in `1..16384`; the default `256` is a good starting point, and notebook examples also use `128`.
- Use `temperature > 0`. Start at `1.0`; lower values reduce diversity, while high values increase noise and unpredictability.
- For prompt adherence versus diversity, tune `supercondition_factor` separately instead of trying to fix everything with temperature.

## Superconditioning over- or under-guides the prompt

Symptoms:

- Prompt seems ignored or too loosely followed.
- Output variety collapses across samples.
- Images become repetitive after increasing guidance.

Recovery:

1. Start with `supercondition_factor=16`.
2. Increase toward `32` when text agreement is more important than variety.
3. Decrease when samples are too similar or over-constrained.
4. Keep `temperature` and `top_k` near defaults while tuning guidance so changes are attributable.

## Stream consumption issues

Symptoms:

- No files appear after creating `image_stream = model.generate_image_stream(...)`.
- Only one final image appears even though a stream API was used.
- `KeyError: 'grid_size'` from `generate_images_stream()`.
- `TypeError` about multiple values for `progressive_outputs`.

Recovery:

1. Iterate the stream; creating the iterator does not run generation to completion.
2. Set `progressive_outputs=True` on stream APIs when intermediate frames are required. Without it, streams yield only the final image.
3. Pass `grid_size=...` as a keyword argument for `generate_images_stream()` and `generate_images()`.
4. Do not pass `progressive_outputs` to `generate_image()` or `generate_images()`; those wrappers force final-only behavior. Use stream methods for progressive output.

## Tensor-to-PIL conversion errors

Symptoms:

- `Image.fromarray()` fails on a tensor batch.
- Saved images are blank, wrong dtype, or still on GPU.
- Code assumes `generate_images()` returns PIL images.

Recovery:

Use the actual tensor contract:

```python
images = model.generate_images(**generation_args)
for i, image_tensor in enumerate(images):
    array = image_tensor.detach().clamp(0, 255).to(torch.uint8).cpu().numpy()
    Image.fromarray(array).save(f"image_{i:02d}.png")
```

`generate_images()` has an imprecise annotation but returns a float tensor batch with shape `(grid_size ** 2, 256, 256, 3)`.

## Seamless output looks unexpected

Symptoms:

- Seamless images do not look like independent samples.
- Splitting a seamless tensor batch into individual images gives unexpected borders or crops.

Cause:

- `is_seamless=True` tiles in token space before detokenization. It is not post-hoc pixel tiling of finished images.

Recovery:

- Use `generate_image(..., is_seamless=True)` when the desired artifact is one tiled grid/texture.
- Use `is_seamless=False` for independent image samples in a grid.
- Be cautious when combining `is_seamless=True` with `generate_images()`; the returned individual images are parts of the seamless global image.

## Seed does not reproduce a result

Symptoms:

- Repeated runs differ despite passing `seed`.
- `seed=-1` or `seed=0` behaves randomly.

Recovery:

1. Use a positive integer seed; only `seed > 0` calls `torch.manual_seed(seed)`.
2. Keep `device`, `dtype`, `is_mega`, `grid_size`, `temperature`, `top_k`, and `supercondition_factor` fixed.
3. Expect possible minor backend nondeterminism across different GPUs, PyTorch builds, and dtypes.

## Prompt text is normalized

Symptoms:

- Case, emoji, or non-ASCII characters do not influence generation as expected.
- Long prompts seem truncated.

Cause:

- The tokenizer demojizes text, lowercases it, drops non-ASCII characters, and truncates to `64` text tokens.

Recovery:

- Rewrite prompts in plain ASCII words when exact wording matters.
- Put the most important concepts early in long prompts.
