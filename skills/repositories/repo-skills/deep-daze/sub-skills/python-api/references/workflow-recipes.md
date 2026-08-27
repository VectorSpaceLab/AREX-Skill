# Deep Daze Python workflow recipes

These recipes assume `deep-daze` is installed in a usable runtime. Construction of `Imagine` loads CLIP, and calling the instance starts optimization. Use `open_folder=False` for noninteractive runs.

## Control the output directory

Deep Daze writes images, progress frames, story transition logs, GIFs, and videos in the current working directory. Wrap calls when the caller needs a predictable output location.

```python
from contextlib import contextmanager
from pathlib import Path
import os

@contextmanager
def working_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    old = Path.cwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(old)
```

## Text-to-image from Python

```python
from deep_daze import Imagine

text = "a house in the forest"

with working_directory("outputs/house"):
    imagine = Imagine(
        text=text,
        epochs=1,
        iterations=250,
        save_every=50,
        save_progress=True,
        open_folder=False,
    )
    imagine()
    print(imagine.filename)
```

## Image-only target

Use `img` when the optimization target is an image interpretation.

```python
from deep_daze import Imagine

imagine = Imagine(
    img="input.png",
    epochs=1,
    iterations=250,
    open_folder=False,
)
imagine()
```

`img` can also be an already loaded image object accepted by torchvision image transforms.

## Combined text and image target

When both `text` and `img` are supplied, Deep Daze averages their CLIP encodings.

```python
from deep_daze import Imagine

imagine = Imagine(
    text="a watercolor forest at dawn",
    img="reference.png",
    averaging_weight=0.3,
    epochs=1,
    iterations=250,
    open_folder=False,
)
imagine()
```

## Custom CLIP encoding

Pass a precomputed CLIP encoding when the target should not be created from `text` or `img`. The tensor must match the selected CLIP model embedding size and is moved to the active device during construction.

```python
from deep_daze import Imagine

encoding = make_custom_clip_encoding_somehow()

imagine = Imagine(
    clip_encoding=encoding,
    epochs=1,
    iterations=250,
    open_folder=False,
)
imagine()
```

To change targets after construction, use `set_clip_encoding`. Remember that output names are not automatically recalculated.

```python
imagine.set_clip_encoding(text="a new target prompt")
imagine.textpath = "a_new_target_prompt"
imagine.filename = imagine.image_output_path()
```

## Start-image priming

Use `start_image_path` when an initial image should prime the SIREN weights before normal optimization.

```python
from deep_daze import Imagine

imagine = Imagine(
    text="a clear night sky filled with stars",
    start_image_path="cloudy-night-sky.jpg",
    start_image_train_iters=50,
    start_image_lr=3e-4,
    epochs=1,
    iterations=250,
    open_folder=False,
)
imagine()
```

Use `img` instead of `start_image_path` when the image itself is the CLIP target. Use both only when the initial appearance and target semantics are intentionally different.

## Story mode for long prose

Story mode changes the CLIP target between epochs. Save progress to see transitions.

```python
from deep_daze import Imagine

story = "the ship leaves port | a storm arrives | dawn breaks over calm water"

imagine = Imagine(
    text=story,
    create_story=True,
    story_separator="|",
    save_progress=True,
    save_every=50,
    epochs=10,          # overwritten by story segmentation
    iterations=250,
    open_folder=False,
)
imagine()
```

Without a separator, use sliding word windows:

```python
imagine = Imagine(
    text="a long paragraph of narrative text goes here",
    create_story=True,
    story_start_words=5,
    story_words_per_epoch=5,
    save_progress=True,
    open_folder=False,
)
```

## Progress frames, final images, GIFs, and video

```python
from deep_daze import Imagine

imagine = Imagine(
    text="crystal city sunrise",
    save_every=25,
    save_progress=True,
    save_gif=True,
    save_video=False,
    open_folder=False,
)
imagine()
```

Progress frames are saved only when `save_progress=True` and `iteration % save_every == 0`. GIF or video generation at the end also requires `save_progress=True`.

## Output path helpers

```python
imagine = Imagine(text="quiet lake", open_folder=False)

print(imagine.textpath)                         # quiet_lake
print(imagine.image_output_path())              # quiet_lake.jpg
print(imagine.image_output_path(12))            # quiet_lake.000012.jpg
print(imagine.get_img_sequence_number(2, 50))   # uses epochs, iterations, save_every
```

Avoid `save_every=0`; sequence-number and progress-save logic divide or modulo by `save_every`.

## Optimizer selection

```python
Imagine(text="default", optimizer="AdamP", open_folder=False)
Imagine(text="torch adam", optimizer="Adam", open_folder=False)
Imagine(text="diffgrad", optimizer="DiffGrad", open_folder=False)
```

Validate optimizer names before construction when accepting user input:

```python
VALID_OPTIMIZERS = {"AdamP", "Adam", "DiffGrad"}
if optimizer not in VALID_OPTIMIZERS:
    raise ValueError(f"optimizer must be one of {sorted(VALID_OPTIMIZERS)}")
```

## Deterministic seed recipe

```python
imagine = Imagine(
    text="repeatable prompt",
    seed=1234,
    epochs=1,
    iterations=250,
    open_folder=False,
)
```

The constructor seeds Torch, CUDA Torch, Python `random`, and requests deterministic cuDNN behavior. Exact repeatability can still vary with hardware, Torch version, mixed precision, and operations that are not fully deterministic.

## Low, average, and high VRAM presets

Very low VRAM recipe:

```python
imagine = Imagine(
    text=text,
    image_width=256,
    num_layers=16,
    batch_size=1,
    gradient_accumulate_every=16,
    open_folder=False,
)
```

Average VRAM recipe:

```python
imagine = Imagine(
    text=text,
    num_layers=24,
    batch_size=16,
    gradient_accumulate_every=2,
    open_folder=False,
)
```

High VRAM recipe:

```python
imagine = Imagine(
    text=text,
    num_layers=42,
    batch_size=64,
    gradient_accumulate_every=1,
    open_folder=False,
)
```

Primary memory knobs are `image_width`, `batch_size`, `gradient_accumulate_every`, `num_layers`, and CLIP `model_name`. Lowering `batch_size` and `image_width` is usually the fastest way to reduce memory pressure; increasing `gradient_accumulate_every` partly compensates for lower batch sizes at additional runtime cost.

## Direct `DeepDaze` use

Direct `DeepDaze` construction is for advanced callers that already manage CLIP loading and normalization.

```python
from deep_daze import DeepDaze

model = DeepDaze(
    clip_perceptor=perceptor,
    clip_norm=normalize,
    input_res=input_resolution,
    total_batches=epochs * iterations * batch_size * gradient_accumulate_every,
    batch_size=batch_size,
    image_width=512,
    num_layers=16,
)
```

Call `model(text_embed)` to get `(image, loss)` or `model(text_embed, return_loss=False)` to get only the generated image tensor.
