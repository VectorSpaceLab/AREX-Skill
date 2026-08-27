# Generation Workflows

These recipes are for future agents writing Python `MinDalle` API calls. Any call that constructs `MinDalle` or generates images may download/load model assets and consume substantial CPU/GPU memory. Before full generation, confirm cache/network/hardware preconditions with the sibling model-assets/runtime skill, or use the bundled script in dry-run mode.

## Shared call pattern

Always use keyword arguments for generation parameters, especially `grid_size`, because tensor batch wrappers reshape outputs by reading `kwargs["grid_size"]`.

```python
generation_args = dict(
    text="Dali painting of WALL·E",
    seed=-1,
    grid_size=3,
    is_seamless=False,
    temperature=1.0,
    top_k=256,
    supercondition_factor=16,
    is_verbose=False,
)
```

Construct once for repeated calls:

```python
import torch
from min_dalle import MinDalle

model = MinDalle(
    models_root="pretrained",
    dtype=torch.float32,
    device="cuda",      # or "cpu"; None auto-selects cuda if available
    is_mega=True,
    is_reusable=True,   # keep weights resident for repeated prompts
    is_verbose=True,
)
```

For a one-shot or memory-constrained run, consider `is_reusable=False`; it loads generation phases as needed and releases modules between phases, but repeated calls are slower.

## Single PIL grid image

Use `generate_image()` when the desired output is one grid image that can be displayed or saved directly with PIL.

```python
image = model.generate_image(**generation_args)
image.save("generated_grid.png")
```

Expected form: a PIL RGB image with width and height equal to `grid_size * 256`. For example, `grid_size=3` produces a `768×768` grid.

Do not pass `progressive_outputs` to `generate_image()`. Use the stream workflow below when intermediate images are required.

## Tensor batch and individual image saves

Use `generate_images()` when the downstream code needs separate 256×256 images as tensors.

```python
from PIL import Image

images = model.generate_images(**generation_args)
# Actual return: torch.FloatTensor, shape (grid_size ** 2, 256, 256, 3)

for i, image_tensor in enumerate(images):
    array = (
        image_tensor
        .detach()
        .clamp(0, 255)
        .to(torch.uint8)
        .cpu()
        .numpy()
    )
    Image.fromarray(array).save(f"generated_{i:02d}.png")
```

Do not call `Image.fromarray()` directly on the floating GPU tensor. Move it to CPU and convert to `uint8` first.

## Progressive PIL stream display or save

Use `generate_image_stream()` for interactive display or progressive grid outputs. With `progressive_outputs=True`, the implementation yields after every `32` generated image tokens and at the final `256` tokens.

```python
image_stream = model.generate_image_stream(
    **generation_args,
    progressive_outputs=True,
)

for step, image in enumerate(image_stream, start=1):
    image.save(f"generated_step_{step:03d}.png")
```

Notebook display pattern:

```python
from IPython.display import display, update_display

is_first = True
for image in model.generate_image_stream(**generation_args, progressive_outputs=True):
    (display if is_first else update_display)(image, display_id=1)
    is_first = False
```

Stream iterators are one-pass. If a loop is not entered or is consumed elsewhere, no image file is produced. Progressive output also detokenizes multiple times, so it is slower than final-only generation.

## Progressive tensor stream

Use `generate_images_stream()` when each progressive step should be split into individual tensor images.

```python
for step, batch in enumerate(
    model.generate_images_stream(**generation_args, progressive_outputs=True),
    start=1,
):
    for i, image_tensor in enumerate(batch):
        array = image_tensor.detach().clamp(0, 255).to(torch.uint8).cpu().numpy()
        Image.fromarray(array).save(f"generated_step_{step:03d}_{i:02d}.png")
```

This path requires `grid_size` in `generation_args`; positional `grid_size` can cause `KeyError` in the wrapper.

## Seamless tiling

Set `is_seamless=True` when a tiled texture is needed:

```python
image = model.generate_image(
    text="seamless watercolor tile of blue flowers",
    seed=123,
    grid_size=2,
    is_seamless=True,
    temperature=1.0,
    top_k=256,
    supercondition_factor=16,
    is_verbose=False,
)
image.save("seamless_grid.png")
```

Seamless mode tiles in token space before VQGAN detokenization, not by pixel-copying finished images. If later using `generate_images()` with `is_seamless=True`, remember that the split images are crops/tiles of a seamless global grid.

## Dry-run planning with the bundled script

The script is safe by default: without `--run`, it prints the constructor/generation plan and warnings without importing `MinDalle`, constructing a model, or downloading assets.

```bash
python scripts/generation_request_template.py \
  --text "Dali painting of WALL-E" \
  --models-root pretrained \
  --output-dir outputs \
  --image-name dali_grid \
  --grid-size 3 \
  --seed -1 \
  --top-k 256 \
  --temperature 1.0 \
  --supercondition-factor 16 \
  --mega \
  --device cuda \
  --dtype float16 \
  --reusable
```

Add `--run` only after cache/network/device/memory preconditions are acceptable:

```bash
python scripts/generation_request_template.py \
  --run \
  --text "Dali painting of WALL-E" \
  --models-root pretrained \
  --output-dir outputs \
  --image-name dali_grid \
  --grid-size 3 \
  --seed 123 \
  --top-k 256 \
  --temperature 1.0 \
  --supercondition-factor 16 \
  --mega \
  --device cuda \
  --dtype float16 \
  --reusable \
  --progressive-outputs
```

For individual tensor image saves from the smaller model on CPU:

```bash
python scripts/generation_request_template.py \
  --run \
  --text "artificial intelligence" \
  --models-root pretrained \
  --output-dir outputs \
  --image-name ai \
  --grid-size 1 \
  --no-mega \
  --device cpu \
  --dtype float32 \
  --non-reusable \
  --tensor-output
```

See [api-reference.md](api-reference.md) for exact method contracts and [troubleshooting.md](troubleshooting.md) for failure recovery.
