# Deep Daze Python API reference

This reference is self-contained for operating agents using the installed `deep-daze` package. Verified package identity: distribution `deep-daze` version `0.11.1`; `import deep_daze` exports `DeepDaze` and `Imagine`; the console script entry point is `imagine = deep_daze.cli:main`.

## Imports and lightweight probes

```python
from deep_daze import Imagine, DeepDaze
from deep_daze.deep_daze import create_text_path
from deep_daze.clip import available_models, tokenize
```

`tokenize("a house")` returns a tensor with shape `(1, 77)`. Available CLIP model names are:

- `RN50`
- `RN101`
- `RN50x4`
- `ViT-B/32`
- `ViT-L/14`

Default `Imagine` model name is `ViT-B/32`.

## `Imagine` constructor

`Imagine` is the high-level Python interface. Its constructor loads CLIP and builds the SIREN generator, so do not instantiate it just to inspect defaults.

```python
Imagine(
    *,
    text=None,
    img=None,
    clip_encoding=None,
    lr=1e-5,
    batch_size=4,
    gradient_accumulate_every=4,
    save_every=100,
    image_width=512,
    num_layers=16,
    epochs=20,
    iterations=1050,
    save_progress=True,
    seed=None,
    open_folder=True,
    save_date_time=False,
    start_image_path=None,
    start_image_train_iters=10,
    start_image_lr=3e-4,
    theta_initial=None,
    theta_hidden=None,
    model_name="ViT-B/32",
    lower_bound_cutout=0.1,
    upper_bound_cutout=1.0,
    saturate_bound=False,
    averaging_weight=0.3,
    create_story=False,
    story_start_words=5,
    story_words_per_epoch=5,
    story_separator=None,
    gauss_sampling=False,
    gauss_mean=0.6,
    gauss_std=0.2,
    do_cutout=True,
    center_bias=False,
    center_focus=2,
    optimizer="AdamP",
    jit=True,
    hidden_size=256,
    save_gif=False,
    save_video=False,
)
```

### Constructor behavior that affects calls

- If `seed` is not `None`, construction sets `torch.manual_seed`, `torch.cuda.manual_seed`, Python `random.seed`, and `torch.backends.cudnn.deterministic = True`.
- If the active Torch version is not `1.7.1`, `jit=True` is automatically changed to `False` with a status message.
- CLIP is loaded with `model_name`, `jit`, and a device chosen as CUDA when available, else CPU.
- `start_image_path`, when provided, must exist. The image is resized and center-cropped to `image_width` and used for a priming phase before text/image optimization.
- `optimizer` must be exactly `AdamP`, `Adam`, or `DiffGrad`. `AdamP` is the default.
- `filename` is initialized from `image_output_path()` after `textpath` is derived by `create_text_path(...)`.

## `DeepDaze` constructor

`DeepDaze` is the lower-level generator/loss module used by `Imagine`. Use it directly only when you already have a CLIP perceptor, normalization transform, and input resolution.

```python
DeepDaze(
    clip_perceptor,
    clip_norm,
    input_res,
    total_batches,
    batch_size,
    num_layers=8,
    image_width=512,
    loss_coef=100,
    theta_initial=None,
    theta_hidden=None,
    lower_bound_cutout=0.1,
    upper_bound_cutout=1.0,
    saturate_bound=False,
    gauss_sampling=False,
    gauss_mean=0.6,
    gauss_std=0.2,
    do_cutout=True,
    center_bias=False,
    center_focus=2,
    hidden_size=256,
    averaging_weight=0.3,
)
```

Important fields set by construction include `perceptor`, `input_resolution`, `normalize_image`, `image_width`, `batch_size`, `total_batches`, `model`, cutout controls, Gaussian sampling controls, center-bias controls, and `averaging_weight`.

`DeepDaze.forward(text_embed, return_loss=True, dry_run=False)` returns `(image, loss)` by default. With `return_loss=False`, it returns only the normalized image tensor. `dry_run=True` avoids incrementing the internal processed-batch counter.

## Target selection and encoding precedence

`Imagine.create_clip_encoding(text=None, img=None, encoding=None)` chooses the optimization target in this order:

1. `encoding` if provided; it is moved to the active device.
2. Story mode, using `update_story_encoding(epoch=0, iteration=1)`.
3. Combined text and image, averaged as `(text_encoding + img_encoding) / 2`.
4. Text only.
5. Image only.
6. `None` if no target was supplied.

`Imagine.set_clip_encoding(text=None, img=None, encoding=None)` replaces `self.clip_encoding` with a newly created encoding and moves it to the active device. It does not rebuild `textpath` or `filename`; update output names manually if the target changes semantically.

Text encodings use CLIP tokenization and `perceptor.encode_text(...)` under `torch.no_grad()`. Image encodings accept either a path string opened as an image or an already loaded image object that the CLIP transform can process.

## `create_text_path` behavior

`create_text_path(context_length, text=None, img=None, encoding=None, separator=None)` returns a base output name, not a directory.

| Inputs | Result behavior |
| --- | --- |
| `text` | If `separator` is present in `text`, keeps only the substring before the first separator. Replaces spaces with underscores and truncates to `context_length` characters. |
| `img` as a string | Replaces spaces with underscores, removes dotted extensions, and joins the remaining dotted parts. |
| `img` as a non-string | Returns `PIL_img`. |
| no `text` and no `img` | Returns `your_encoding`, including the custom-encoding case. |

Examples:

```python
create_text_path(77, text="a house in the forest")      # "a_house_in_the_forest"
create_text_path(77, text="scene one | scene two", separator="|")  # "scene_one_"
create_text_path(77, img="input image.png")             # "input_image"
create_text_path(77, img=object())                       # "PIL_img"
create_text_path(77, encoding=object())                  # "your_encoding"
```

## Output path and saving methods

`Imagine.image_output_path(sequence_number=None)` returns a `Path` ending in `.jpg`:

- Base name starts with `self.textpath`.
- If `sequence_number` is truthy, it appends a six-digit zero-padded suffix such as `.000012`.
- If `save_date_time=True`, it prepends a timestamp.

`Imagine.get_img_sequence_number(epoch, iteration)` computes `(epoch * iterations + iteration) // save_every`.

`Imagine.save_image(epoch, iteration, img=None)`:

- Computes the sequence number.
- Generates a current image when `img` is `None`.
- Saves both the sequenced frame and the latest `{textpath}.jpg` in the current working directory.
- Updates `self.filename` to the sequenced path.

`Imagine.generate_gif()` scans the current working directory for progress frames whose names start with `textpath`, excludes the latest `{textpath}.jpg`, and writes `{textpath}.gif` and/or `{textpath}.mp4` according to `save_gif` and `save_video`.

## Story mode methods

When `create_story=True`, `text` is required. Construction computes `epochs` from the word window or from separator-delimited segments.

- Without a separator, the first target uses `story_start_words`; each later epoch appends up to `story_words_per_epoch` words.
- With `story_separator`, the separator must appear in the text to define segments; otherwise it is ignored.
- If the text contains only the separator and whitespace, construction exits.
- `update_story_encoding(...)` writes a `story_transitions.txt` file in the current working directory and returns the next text encoding.

## Start-image priming

`start_image_path` is not the same as `img`:

- `start_image_path` primes the generator weights for `start_image_train_iters` using `DiffGrad` and `start_image_lr`, then normal optimization begins.
- `img` is an optimization target encoded by CLIP, optionally averaged with text.
- They can be combined, but they solve different problems.
