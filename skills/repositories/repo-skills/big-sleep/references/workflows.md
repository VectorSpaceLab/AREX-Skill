# Workflows

## Purpose

Read this when you want to run Big Sleep end to end: the `dream` CLI, the Python `Imagine` API, prompt combinations, and output controls.

## Before the first run

1. Run `scripts/check_runtime.py --check-cli`.
2. Confirm `dream --help` works in the installed environment.
3. Use a short smoke run first; the repository defaults are intentionally long (`epochs=20`, `iterations=1050`).

## 1) Minimal text-to-image run

A short smoke run should use a small image size, one epoch, one iteration, and `open_folder=False` when the session is remote or headless. For Fire boolean flags, prefer explicit `=True` / `=False` assignments; do not use space-separated `--open_folder false`.

```bash
dream "a pyramid made of ice" \
  --image_size 128 \
  --epochs 1 \
  --iterations 1 \
  --save_every 1 \
  --num_cutouts 1 \
  --save_best=True \
  --open_folder=False \
  --overwrite=True
```

Why this shape works:

- `--image_size 128` reduces memory pressure.
- `--save_every 1` makes the first update visible immediately.
- `--num_cutouts 1` keeps the smoke run lightweight; remove or raise it for a real-quality run.
- `--save_best=True` checks that the CLIP-scoring path is live.
- `--open_folder=False` avoids desktop/file-manager side effects.

## 2) Multi-prompt and negative-prompt runs

Big Sleep uses `|` inside the prompt string to split multiple phrases. That same delimiter also works for `text_min`.

```bash
dream "an armchair in the form of pikachu|an armchair imitating pikachu|abstract" \
  --text_min "blur|zoom" \
  --max_classes 20 \
  --experimental_resample \
  --num_cutouts 1 \
  --save_best=True \
  --open_folder=False
```

Use this pattern when you want:

- several positive prompts blended in one run,
- a set of suppressive prompts, or
- extra stability from class restriction plus the resampler.

Keep the prompt strings short. CLIP tokenization is capped at 77 tokens, so long sentence fragments are more likely to fail than short prompt phrases.

## 3) Image-conditioned generation

The `img` argument accepts a path string or a PIL image object.

```python
from big_sleep import Imagine

dream = Imagine(
    text="fire in the sky",
    img="reference.png",
    lr=5e-2,
    save_every=25,
    save_progress=True,
    open_folder=False,
)

dream()
```

Use image conditioning when the text prompt should steer an existing image rather than start from scratch.

## 4) Reproducibility and output naming

Useful switches:

- `--seed <n>` for a fixed seed.
- `--random` to pick a random seed in the CLI wrapper.
- `--append_seed` to keep the seed visible in the filename.
- `--save_date_time` to prefix the filename with a timestamp.
- `--overwrite=True` to avoid the interactive overwrite prompt.

Output naming rules worth remembering:

- Spaces become `_`.
- `|` becomes `--`.
- Negative prompts are folded into the filename as a `wout_...` fragment.
- The filename is truncated to stay within common path-length limits.

## 5) Python API control

```python
from big_sleep import Imagine

dream = Imagine(
    text="fire in the sky",
    lr=5e-2,
    save_every=25,
    save_progress=True,
    open_folder=False,
)

dream()

dream.set_text("a quiet pond underneath the midnight moon")
dream.reset()
```

Use `set_text` when you want to reuse the same model state for a new prompt. Use `reset` when you want fresh latents.

## 6) Tuning knobs that change behavior

| Flag / argument | When to reach for it |
| --- | --- |
| `--bilinear` | Smoother cutout interpolation; avoid with `--torch_deterministic`. |
| `--torch_deterministic` | Reproducibility-focused runs when you are not using bilinear interpolation. |
| `--max_classes` | Restrict BigGAN to a smaller class set for extra stability. |
| `--class_temperature` | Tune the softness of class selection. |
| `--ema_decay` | Adjust the moving-average memory of the latent parameters. |
| `--num_cutouts` | Increase or decrease the number of CLIP cutouts used in the loss. |
| `--center_bias` | Bias cutouts toward the image center. |
| `--experimental_resample` | Use the bundled differentiable resampler instead of plain interpolation. |
| `--larger_model` | Switch the CLIP perceptor from `ViT-B/32` to `ViT-L/14`. |

## 7) Full run versus smoke run

The README examples use longer defaults such as `epochs=20` and `iterations=1050`. That is the real generation path, but it is too expensive for quick verification. For inspection or verification work, reduce the step count first, then increase it only after the pipeline is healthy.

A good progression is:

1. `dream --help`
2. `scripts/check_runtime.py`
3. a one-step smoke run
4. a longer prompt run if you actually want an output worth keeping

## 8) What to expect on disk

- PNGs are written into the current working directory.
- `save_progress` adds numbered snapshots.
- `save_best` writes a `.best.png` only when a better score appears.
- `open_folder` may open the directory automatically on desktop systems.

If the output directory already contains the target filename and you did not pass `--overwrite`, the CLI asks before replacing it.
