# Deep Daze Python API troubleshooting

Use this guide for code-level failures after the package imports. Route installation, CLIP cache/download, network, CUDA driver, and backend availability issues to [../../runtime-and-models/SKILL.md](../../runtime-and-models/SKILL.md). Route shell quoting and command construction issues to [../../cli-workflows/SKILL.md](../../cli-workflows/SKILL.md).

## Constructor triggers CLIP loading or downloads

Symptom: `Imagine(...)` is slow, prints model-loading messages, downloads model weights, or fails before optimization begins.

Cause: `Imagine` loads CLIP during construction. It is not a lightweight object.

Fixes:

- Use `scripts/probe_api_surface.py --verify` for signature/default checks without constructing `Imagine`.
- Instantiate only after selecting `model_name`, device expectations, output directory, and memory settings.
- Keep API code free of hidden constructor calls in tests that only need metadata.
- For cache, network, or hardware diagnosis, route to [../../runtime-and-models/SKILL.md](../../runtime-and-models/SKILL.md).

## Image path and image-object failures

Symptom: assertion failure for a starting image path, image-open errors, transform errors, or a missing output name.

Key distinction:

- `start_image_path` primes the generator and asserts that the path exists during construction.
- `img` is the CLIP image target. If it is a string, it is opened as an image; if it is not a string, it must already be image-like for the transform pipeline.

Fixes:

- Resolve paths relative to the current working directory used by the Python process.
- Validate `Path(start_image_path).exists()` before constructing `Imagine`.
- Validate `Path(img).exists()` yourself when `img` is a string; `img` does not use the same assertion path as `start_image_path`.
- Use RGB-compatible images when passing loaded image objects.

## Text, image, and `clip_encoding` selection surprises

Symptom: target appears to ignore text or image, or `set_clip_encoding(...)` fails with an attribute error.

Selection order is `clip_encoding`, story mode, combined text+image, text-only, image-only, then `None`. A supplied custom encoding replaces text/image target creation. If no target is supplied, later code receives `None` and fails.

Fixes:

- Require at least one of `text`, `img`, or `clip_encoding` unless the code sets a valid target before training.
- Do not pass `clip_encoding` accidentally alongside text/image unless replacement is intended.
- After `set_clip_encoding(...)`, update `textpath` and `filename` yourself if output names should reflect the new target.
- Validate custom encodings for dtype, shape, and device compatibility before training.

## Story mode assertions and separators

Symptom: construction asserts, exits, creates unexpected epoch counts, or story transitions are odd.

Rules:

- `create_story=True` requires `text`.
- Text that consists only of the separator and whitespace exits early.
- A provided separator is ignored if it is not present in the text.
- With a valid separator, epochs are based on non-empty separator-delimited segments.
- Without a separator, epochs are based on `story_start_words` and `story_words_per_epoch`.
- Story transitions are written to `story_transitions.txt` in the current working directory.

Fixes:

- Validate `text.strip()` and separator placement before construction.
- Prefer clear segment separators such as `|` for paragraph-level storyboarding.
- Keep each segment short enough for CLIP tokenization even in story mode.
- Use a clean output directory per story run to avoid mixing transition logs and progress frames.

## Prompt length and tokenization failures

Symptom: `RuntimeError: Input ... is too long for context length 77`.

Cause: regular text encoding uses CLIP tokenization with context length 77. `tokenize("a house")` has shape `(1, 77)`, and longer prompts can exceed that fixed context length.

Fixes:

```python
from deep_daze.clip import tokenize

def assert_clip_prompt_fits(text):
    tokenize(text)  # raises RuntimeError if too long
```

- Shorten regular prompts.
- Split long prose with `create_story=True` and a separator.
- Still validate story segments; story mode changes the target over epochs but does not make CLIP accept arbitrarily long segment encodings.

## Optimizer-name errors

Symptom: training fails when stepping the optimizer, or `self.optimizer` is missing.

Cause: only exact optimizer strings are handled: `AdamP`, `Adam`, and `DiffGrad`. Unknown names do not fall back to a default.

Fix:

```python
valid = {"AdamP", "Adam", "DiffGrad"}
if optimizer not in valid:
    raise ValueError(f"optimizer must be one of {sorted(valid)}")
```

## `save_every`, `save_progress`, GIF, and video behavior

Symptoms: no progress frames, modulo/division errors, empty animation, or only a final image.

Rules:

- `save_every` is used both for modulo checks and sequence-number division; do not set it to `0`.
- Intermediate frames save only when `save_progress=True` and `iteration % save_every == 0`.
- A final image is saved at the end of `forward()` even when progress saving is disabled.
- GIF/video generation runs only when `save_progress=True` and `save_gif` or `save_video` is set.
- `generate_gif()` scans the current working directory for files beginning with `textpath`; stale frames can be included if outputs are mixed.

Fixes:

- Use a fresh output directory per run.
- Set `save_progress=True` when requesting `save_gif=True` or `save_video=True`.
- Choose `save_every` less than or equal to `iterations` for at least one progress frame per epoch.
- Remove stale frames with the same `textpath` before generating animations.

## Seed determinism is bounded

Symptom: same `seed` gives slightly different outputs across machines or runs.

Behavior: construction seeds Torch CPU, Torch CUDA, and Python `random`, and requests deterministic cuDNN. It does not seed NumPy, and full determinism can still depend on hardware, Torch version, precision settings, and operation-level determinism.

Fixes:

- Set `seed` in `Imagine`.
- If surrounding code uses NumPy, seed NumPy as well.
- Keep Torch, CUDA, model, and hardware settings consistent when comparing outputs.
- Treat exact pixel equality as stronger than the API promises; compare output existence and coarse properties unless strict determinism has been proven in the target runtime.

## CPU slowness and GPU memory pressure

Symptoms: runs appear hung on CPU, CUDA out-of-memory, or optimization is too slow.

Facts:

- CPU execution can be extremely slow because every iteration performs CLIP image encoding and SIREN optimization.
- Memory pressure is controlled mainly by `image_width`, `batch_size`, `gradient_accumulate_every`, `num_layers`, `hidden_size`, and `model_name`.

Fixes:

- For a quick smoke run, reduce `epochs`, `iterations`, `image_width`, `batch_size`, and `num_layers`.
- For very low VRAM, start with `image_width=256`, `num_layers=16`, `batch_size=1`, and `gradient_accumulate_every=16`.
- For better quality on high VRAM, increase `num_layers` and `batch_size` while keeping `gradient_accumulate_every` low.
- If the issue is driver, backend, CLIP cache, or package compatibility, route to [../../runtime-and-models/SKILL.md](../../runtime-and-models/SKILL.md).

## Output-name collisions

Symptom: files are overwritten or frames from different runs are mixed.

Causes:

- Output names are derived from `text`, `img`, or `your_encoding`.
- `save_date_time=False` by default.
- `set_clip_encoding(...)` does not update `textpath`.
- `generate_gif()` includes matching files in the current working directory.

Fixes:

- Use a separate output directory for each run.
- Enable `save_date_time=True` when repeated prompts should produce distinct filenames.
- Manually update `textpath` and `filename` after target replacement.
- Clean old progress frames before animation generation.
