# Data Formats

This reference summarizes the tensor shapes and value conventions used by the rich-media summary APIs.

## Images

| Input form | Meaning | Notes |
| --- | --- | --- |
| `CHW` | single image | default for `add_image()` |
| `NCHW` | batch of images | default for `add_images()` |
| `HWC` | single image in height-width-channel order | accepted when `dataformats='HWC'` |
| `HW` | grayscale image | expanded to RGB internally |

Rules:

- Float image tensors are scaled to `uint8` by multiplying by 255.
- `uint8` images are treated as already being in `[0, 255]`.
- Channel counts of 1, 3, or 4 are the practical cases exercised by the repo.
- `add_image_with_boxes()` expects box coordinates in `xyxy` order.

## Figures

- Use a `matplotlib.pyplot.figure` object or a list of figures.
- The helper renders the figure to an image array and closes it by default.
- Keep figures small and deterministic if you want a smoke test.

## Audio

| Field | Contract |
| --- | --- |
| shape | 1-D array or tensor |
| values | expected in `[-1, 1]` |
| sample rate | integer Hz, default `44100` |

The summary writer encodes the signal as audio; it does not infer sample rate or clip protection for you.

## Video

| Input form | Meaning |
| --- | --- |
| `NTCHW` | default for `add_video()` |
| `T, N, C, H, W` | canonical order after conversion |

Rules:

- Video input is 5-D before conversion.
- `moviepy`/`imageio` encode the frames to a GIF-backed summary.
- 1-channel video may be converted to RGB depending on the installed moviepy/imageio combination.

## Histograms

- Accepts numeric values of any shape.
- Empty input is invalid.
- `bins='tensorflow'`, `'auto'`, `'fd'`, or `'doane'` are the useful modes seen in the repo tests.
- `max_bins` caps histogram resolution.

## PR curves

| Input | Meaning |
| --- | --- |
| `labels` | binary ground-truth values |
| `predictions` | model scores or probabilities |
| `weights` | optional per-example weights |

The helper expects labels and predictions to be aligned arrays. Use the raw variant only when you already have the bucket counts.

## Meshes

- `vertices` should be shaped like `[N, V, 3]` for `N` meshes and `V` vertices.
- `colors` should match the mesh vertex layout when provided.
- `faces` should index vertex triples.
- `config_dict` lets you pass mesh viewer options.

## Text

- Plain strings and Markdown are both acceptable.
- Keep the text small and readable when you use it in a smoke script.

## When shape validation fails

- Re-check the input layout string first.
- Then confirm dtype, rank, and channel count.
- If the issue is still unclear, run the bundled smoke script and compare its tiny fixture with your data.
