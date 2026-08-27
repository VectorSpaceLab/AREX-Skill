# DreamCraft3D Image Inputs

## Purpose

Read this when preparing or checking the single reference image consumed by the DreamCraft3D stage configs.

## Expected sidecar layout

DreamCraft3D's canonical configs use `data_type: single-image-datamodule`. The datamodule loads one RGBA image and, depending on config flags, looks for depth and normal files by replacing the `_rgba.png` suffix:

| Input file | Required by | How it is used |
| --- | --- | --- |
| `<stem>_rgba.png` | all canonical stages | RGB supervision plus alpha mask. The datamodule reads the file with unchanged channels and converts BGRA to RGBA. |
| `<stem>_depth.png` | coarse NeRF, coarse NeuS, and geometry when depth losses are active | Reference depth map. The datamodule asserts the sidecar exists when `requires_depth` is true. |
| `<stem>_normal.png` | stages where `requires_normal` resolves true | Reference normal map. It is loaded as a three-channel image and normalized to `[0,1]`. |
| `<stem>_caption.txt` | optional | Created only when captioning is requested; not required by the canonical training configs. |

Example ready image family:

```text
load/images/mushroom_log_rgba.png
load/images/mushroom_log_depth.png
load/images/mushroom_log_normal.png
load/images/mushroom_log_caption.txt   # optional
```

## Preprocessing command

The repository preprocessing script accepts a file or a directory of PNG files:

```bash
python preprocess_image.py input.png --recenter
```

Important options:

| Option | Meaning |
| --- | --- |
| `path` | Image file or directory. Directory mode processes PNGs that do not already end in `_rgba.png`, `_depth.png`, or `_normal.png`. |
| `--size` | Output square size when recentering; default `1024`. |
| `--border_ratio` | Border reserved around the object during recentering; default `0.1`. |
| `--recenter` | Crops the foreground mask, rescales it into a square canvas, and writes recentered RGBA/depth/normal outputs. |
| `--do_caption` | Runs BLIP2 captioning and writes `<stem>_caption.txt`; this is slower and requires extra model weights. |

Preprocessing writes outputs beside the input image. For `input.png`, it creates `input_rgba.png`, `input_depth.png`, and `input_normal.png`.

## Model and backend requirements

Full preprocessing is not just a file conversion:

- Background removal uses CarveKit's `HiInterface` on CUDA by default.
- Depth and normal prediction use Omnidata DPT checkpoints expected under `load/omnidata/`.
- Optional captioning uses `Salesforce/blip2-opt-2.7b`, `transformers`, and enough memory to load BLIP2.
- The script imports OpenCV, torch, torchvision transforms, PIL, matplotlib, and NumPy at module import time.

Use the bundled validator when you only need to check sidecars; it does not replace full preprocessing.

## Feeding sidecars into stages

After preprocessing, pass the RGBA image path as a config override:

```bash
data.image_path="load/images/mushroom_log_rgba.png"
```

The stage configs derive sidecar paths from that value. If a config requires depth or normal and the sidecar is missing, the datamodule asserts before training can proceed.

## Validation examples

Check the common coarse-stage requirements:

```bash
python <skill-dir>/sub-skills/image-preparation/scripts/validate_preprocessed_image.py \
  --image load/images/mushroom_log_rgba.png --require-depth --require-normal
```

Get a planning report without failing on missing sidecars:

```bash
python <skill-dir>/sub-skills/image-preparation/scripts/validate_preprocessed_image.py \
  --image input_rgba.png --require-depth --require-normal --allow-missing --json
```

## Practical guidance

- Prefer reusing existing `_rgba`, `_depth`, and `_normal` files when they are aligned to the same stem.
- Do not point `data.image_path` at the original RGB input after preprocessing; use the `_rgba.png` output.
- If the user changes recentering size or border ratio, regenerate all sidecars together so RGB, depth, normal, and mask stay aligned.
- Treat captioning as optional metadata. A good human-written prompt is often safer than running BLIP2 solely to satisfy DreamCraft3D.
