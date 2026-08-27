# Portrait Workflow API and CLI Reference

## Bundled scripts

### `scripts/portrait_infer.py`

Purpose: produce portrait-map PNGs from image folders.

Important options:

| Option | Meaning |
| --- | --- |
| `--mode {portrait-set,own-images}` | `portrait-set` uses 512 RGB preprocessing for already cropped portraits; `own-images` uses OpenCV face detection and crop/pad/resize. |
| `--weights PATH` | `u2net_portrait.pth`-compatible state dict. Required unless random smoke mode is enabled. |
| `--input-dir DIR` | Top-level image directory. Common image extensions are filtered. |
| `--output-dir DIR` | Destination for portrait PNGs. Created if missing. |
| `--cascade PATH` | Haar cascade XML for own-image mode; defaults to bundled XML. |
| `--device {auto,cpu,cuda}` | Device selection. Explicit CUDA fails if unavailable. |
| `--max-images N` | Bounds a smoke or sample run after sorted input collection. |
| `--allow-random-weights-for-smoke` | Runs without weights for plumbing only. |

Output: one grayscale uint8 PNG per processed image, named `<input-stem>.png`. The JSON summary reports processed count, device, random-weight status, outputs, skipped non-image files, and warnings.

### `scripts/portrait_composite.py`

Purpose: generate portrait/original composites.

Important options:

| Option | Meaning |
| --- | --- |
| `--weights PATH` | `u2net_portrait.pth`-compatible state dict. Required unless random smoke mode is enabled. |
| `--input-dir DIR` | Top-level image directory. |
| `--output-dir DIR` | Destination for composite PNGs. |
| `--sigma FLOAT` | Gaussian blur sigma for the original image; must be `>= 0`. |
| `--alpha FLOAT` | Blend weight for the blurred original image; must be in `[0,1]`. |
| `--device {auto,cpu,cuda}` | Device selection. |
| `--max-images N` | Bounds runtime. |
| `--allow-random-weights-for-smoke` | Plumbing-only run without weights. |

Output filename pattern: `<input-stem>_sigma_<sigma>_alpha_<alpha>_composite.png`, with punctuation sanitized by the helper.

## Model and preprocessing facts

- Portrait workflows use `U2NET(3,1)`, not `U2NETP`.
- Portrait maps use `1.0 - fused_output` before normalization.
- Portrait-set mode uses RGB preprocessing at 512x512.
- Own-image mode uses BGR OpenCV loading and the source demo's BGR channel normalization after face crop/pad/resize.
- Compositing uses RGB original image blur plus a portrait-gray channel broadcast into RGB blending.

## Haar cascade asset

The generated skill bundles `scripts/haarcascade_frontalface_default.xml`, copied from the repository's OpenCV face-detection asset. If a user supplies a custom cascade, verify the XML exists and OpenCV can load it before processing images.
