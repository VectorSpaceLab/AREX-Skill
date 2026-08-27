# Usage Overview

## When to read this

Read this after the root router when you need a compact map of Deep Daze's
surfaces before choosing the CLI, Python API, or runtime/model sub-skill.

## Package concept map

Deep Daze is a CLIP-guided image-generation package:

- `deep_daze.Imagine` is the high-level Python module most users call. It loads
  CLIP, creates a `DeepDaze` Siren generator, builds a text/image/encoding target,
  runs optimization, and saves images.
- `deep_daze.DeepDaze` is the lower-level Siren generator wrapper. It expects an
  already loaded CLIP perceptor, normalization transform, input resolution,
  total-batch count, and batch settings.
- `deep_daze.clip` vendors CLIP model definitions, tokenization, model-name
  registry, checkpoint download/checksum handling, and the BPE tokenizer data.
- `imagine` is the console script. It wraps `Imagine` through a Fire CLI and maps
  command-line flags to constructor arguments.

## Common workflow choices

| Goal | Preferred surface | Notes |
|---|---|---|
| Quick text prompt from a shell | `imagine "prompt"` | Use `--open_folder=False` in headless sessions and small resource settings for first runs. |
| Image-only interpretation | `imagine --img image.jpg` | The image is encoded by CLIP as the optimization target. |
| Text + image target | `imagine "prompt" --img image.jpg` or `Imagine(text=..., img=...)` | Deep Daze averages text and image encodings. |
| Start-image priming | `--start_image_path image.jpg` or `Imagine(start_image_path=...)` | Priming trains the Siren toward the image before text/image optimization. |
| Long poem/story | `--create_story=True` or `Imagine(create_story=True, ...)` | Use progress saving; normal CLIP text context is 77 tokens. |
| Programmatic adaptation | `deep_daze.Imagine` | Use the Python API sub-skill for exact defaults and method behavior. |
| Runtime diagnosis | bundled inspection scripts | Safe checks avoid CLIP checkpoint downloads and generation. |

## Output and side effects

Generation writes files relative to the current working directory:

- Final image: `<sanitized_text_or_image_stem>.jpg`.
- Progress frames: `<stem>.<sequence>.jpg` when `save_progress=True` and the
  iteration is a multiple of `save_every`.
- Timestamped files: enabled by `save_date_time=True`.
- Story mode: updates text per epoch and writes `story_transitions.txt`.
- GIF/video: generated from progress frames when `save_gif=True` or
  `save_video=True`, and only when progress frames exist.

The CLI may ask before overwriting an existing final output unless
`--overwrite=True` is supplied. In automated runs, prefer timestamped outputs or
an empty output directory over broad overwrites.

## Runtime expectations

- The package imports on CPU-capable Python environments when dependencies are
  installed, but practical generation is much more realistic on a PyTorch
  accelerator with enough memory.
- CLIP checkpoints are downloaded lazily by `deep_daze.clip.load` when a model
  name is first used and not already cached.
- `Imagine` sets `jit=False` automatically unless the torch version string
  contains `1.7.1`, because the vendored CLIP JIT path is version-sensitive.
- The default optimizer is `AdamP`; accepted optimizer names in source are
  `AdamP`, `Adam`, and `DiffGrad`.

## Where details live

- Runtime and CLIP/cache details: `sub-skills/runtime-and-models/`.
- CLI flags, commands, and command builder: `sub-skills/cli-workflows/`.
- Python signatures, recipes, and API probe: `sub-skills/python-api/`.
