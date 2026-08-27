# API Reference

## Purpose

Read this when you need exact Big Sleep signatures, defaults, and object behavior without reopening the source tree.

## Verified public entry points

The package exports the main user-facing types from `big_sleep`:

- `BigSleep`
- `Imagine`

The CLI entry point is `dream`, which wraps `big_sleep.cli.train` through Fire.

## Verified signatures

### `big_sleep.cli.train`

```python
train(
    text=None,
    img=None,
    text_min="",
    lr=0.07,
    image_size=512,
    gradient_accumulate_every=1,
    epochs=20,
    iterations=1050,
    save_every=50,
    overwrite=False,
    save_progress=False,
    save_date_time=False,
    bilinear=False,
    open_folder=True,
    seed=0,
    append_seed=False,
    random=False,
    torch_deterministic=False,
    max_classes=None,
    class_temperature=2.0,
    save_best=False,
    experimental_resample=False,
    ema_decay=0.5,
    num_cutouts=128,
    center_bias=False,
    larger_model=False,
)
```

Notes:

- `random=True` replaces the supplied seed with a random integer.
- `larger_model=True` maps to the `larger_clip` path in `Imagine`.
- The Fire CLI prints underscore flag names such as `--save_progress`, `--save_best`, `--open_folder`, `--text_min`, and `--max_classes`.

### `big_sleep.Imagine`

```python
Imagine(
    *,
    text=None,
    img=None,
    encoding=None,
    text_min="",
    lr=0.07,
    image_size=512,
    gradient_accumulate_every=1,
    save_every=50,
    epochs=20,
    iterations=1050,
    save_progress=False,
    bilinear=False,
    open_folder=True,
    seed=None,
    append_seed=False,
    torch_deterministic=False,
    max_classes=None,
    class_temperature=2.0,
    save_date_time=False,
    save_best=False,
    experimental_resample=False,
    ema_decay=0.99,
    num_cutouts=128,
    center_bias=False,
    larger_clip=False,
)
```

Important behavior:

- Construction immediately loads CLIP and BigGAN, moves the model to CUDA, and prepares the latent optimizer.
- Calling the instance runs generation and writes PNG files into the current working directory.
- `seed=None` means no explicit manual seed; the CLI wrapper uses `seed=0` unless `--random` is set.
- `save_progress` writes numbered intermediate images.
- `save_best` writes `{prompt}.best.png` when the CLIP score improves.
- `open_folder=True` may open the output directory through the local desktop file manager.

### `big_sleep.BigSleep`

```python
BigSleep(
    num_cutouts=128,
    loss_coef=100,
    image_size=512,
    bilinear=False,
    max_classes=None,
    class_temperature=2.0,
    experimental_resample=False,
    ema_decay=0.99,
    center_bias=False,
    larger_clip=False,
)
```

Lower-level behavior:

- This is the generator/perceptor wrapper used by `Imagine`.
- `forward(text_embeds, text_min_embeds=[], return_loss=True)` returns the generated image batch plus the latent/class/similarity losses.
- `return_loss=False` returns only the generated image batch.
- The class is useful if you need to build your own optimization loop.

### `Imagine` helper methods

```python
Imagine.set_text(text)
Imagine.reset()
```

- `set_text` replaces the active positive prompt and rebuilds prompt encodings.
- `reset` reinitializes the latent state and optimizer.

## Behavior details that matter in practice

| Surface | Verified behavior |
| --- | --- |
| `text` | A single string may contain `|` to split into multiple positive prompts. |
| `text_min` | The same `|` delimiter applies to negative prompts. |
| `img` | May be a path string or a PIL image. If both text and image are given, `Imagine` averages the two encodings. |
| `image_size` | Must be one of `128`, `256`, or `512`. |
| `max_classes` | Must be between `1` and `1000` when provided. |
| `torch_deterministic` | Requires `bilinear=False`; the code asserts otherwise. |
| `save_date_time` | Prefixes the filename with a timestamp. |
| `append_seed` | Adds `.seed` to the output filename when a seed exists. |
| `overwrite` | If false and the output file already exists, the CLI prompts before replacing it. |
| `save_best` | Depends on improving score; a `.best.png` file may never appear if later scores do not improve. |
| `center_bias` | Biases cutout sampling toward the image center. |
| `experimental_resample` | Uses the bundled differentiable resampler instead of plain interpolation. |
| `larger_model` / `larger_clip` | Switches from `ViT-B/32` to `ViT-L/14`. |

## Suggested read order

1. `references/workflows.md` for concrete run recipes.
2. `references/troubleshooting.md` for runtime failures and recovery paths.
3. `scripts/check_runtime.py` when you need a quick environment check before running a generation job.
