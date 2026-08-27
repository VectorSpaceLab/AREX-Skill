# Dataset Format Reference

ControlNet tutorial training expects a Fill50K-style paired dataset: one control/source image, one target image, and one text prompt per row. The dataset object returns keys that match the model config keys: `first_stage_key: jpg`, `cond_stage_key: txt`, and `control_key: hint`.

## Directory Layout

A Fill50K dataset root contains:

```text
fill50k/
  prompt.json
  source/
    0.png
    1.png
  target/
    0.png
    1.png
```

The tutorial examples use `training/fill50k` as the dataset root. Custom datasets can use any path if the training script points `MyDataset` or its replacement at that path.

## `prompt.json` Schema

`prompt.json` is JSON Lines, not one large JSON array. Each non-empty line is one object:

```json
{"source": "source/0.png", "target": "target/0.png", "prompt": "cyan circle with pink background"}
{"source": "source/1.png", "target": "target/1.png", "prompt": "orange circle with black background"}
```

Required keys:

| Key | Type | Meaning |
| --- | --- | --- |
| `source` | string | Relative path from the dataset root to the control image, such as `source/123.png`. |
| `target` | string | Relative path from the dataset root to the target image, such as `target/123.png`. |
| `prompt` | string | Text condition returned as `txt`. Empty strings are technically loadable but should be treated as suspicious for prompt-conditioned training. |

Do not rename these schema keys unless the custom `Dataset` translates them back to the model-facing keys `jpg`, `txt`, and `hint`.

## `MyDataset` Contract

The tutorial `MyDataset` behavior can be reproduced without importing the original file:

1. Read `prompt.json` line by line and parse each line as JSON.
2. For item `idx`, load `source` and `target` with OpenCV.
3. Convert OpenCV BGR arrays to RGB before normalization.
4. Normalize the source/control image to `float32` in `[0, 1]`.
5. Normalize the target image to `float32` in `[-1, 1]` using `(pixel / 127.5) - 1.0`.
6. Return `dict(jpg=target, txt=prompt, hint=source)`.

The model configs expect these names:

| Returned key | Config key | Expected content |
| --- | --- | --- |
| `jpg` | `first_stage_key` | Target RGB image normalized to `[-1, 1]`. |
| `txt` | `cond_stage_key` | Prompt string. |
| `hint` | `control_key` | Control/source RGB image normalized to `[0, 1]`. |

## Shape And Range Expectations

The Fill50K tutorial test prints `jpg.shape` and `hint.shape` as `(512, 512, 3)`. Custom training can use other sizes only when the model/training pipeline handles resizing or compatible dimensions. For the original tutorial path, use RGB images with matching source/target dimensions and three channels.

Expected value ranges after normalization:

| Array | Minimum | Maximum | Notes |
| --- | --- | --- | --- |
| `hint` | `0.0` | `1.0` | Source/control image after `source.astype(np.float32) / 255.0`. |
| `jpg` | `-1.0` | `1.0` | Target image after `(target.astype(np.float32) / 127.5) - 1.0`. |

If a custom dataset returns PIL or NumPy arrays directly, verify channel order and ranges before starting training. BGR/RGB mistakes often do not crash; they silently train on color-swapped data.

## Tiny Valid Example

```text
fill50k/
  prompt.json
  source/0.png
  target/0.png
```

`prompt.json`:

```json
{"source": "source/0.png", "target": "target/0.png", "prompt": "blue circle on white background"}
```

Validation expectations:

- `prompt.json` exists and contains valid JSON Lines.
- Every row has exactly the required semantic keys: `source`, `target`, and `prompt`.
- Every referenced image path stays inside the dataset root.
- Source and target images are readable by common image libraries.
- Source and target images are RGB-compatible, three-channel images.
- Source and target dimensions match unless the custom training transform intentionally resizes them.
- Tutorial-style normalized arrays would produce `hint` in `[0, 1]` and `jpg` in `[-1, 1]`.

Use `../scripts/validate_fill50k_dataset.py --write-example-fixture <dir> --validate-written-fixture` to create a tiny local fixture with these properties.
