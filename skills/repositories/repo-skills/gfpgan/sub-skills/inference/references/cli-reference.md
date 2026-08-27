# GFPGAN Inference CLI Reference

## Purpose

Read this when mapping user requests to GFPGAN inference flags or when adapting the bundled `scripts/run_inference.py` helper.

## Verified Source CLI Flags

The repository's public inference script exposes these flags:

| Flag | Default | Meaning |
| --- | --- | --- |
| `-i`, `--input` | `inputs/whole_imgs` | Input image file or folder. |
| `-o`, `--output` | `results` | Output folder. |
| `-v`, `--version` | `1.3` | Model version: `1`, `1.2`, `1.3`, `1.4`, or `RestoreFormer` in current source logic. |
| `-s`, `--upscale` | `2` | Final upsampling scale. |
| `--bg_upsampler` | `realesrgan` | Background upsampler selection in the source script. The bundled helper defaults to no background upsampler for safer operation. |
| `--bg_tile` | `400` | Tile size for Real-ESRGAN background upsampling; `0` means no tile. |
| `--suffix` | `None` | Optional suffix added to restored face/image output filenames. |
| `--only_center_face` | `False` | Restore only the center face. |
| `--aligned` | `False` | Treat inputs as already aligned face crops. |
| `--ext` | `auto` | Output extension: `auto`, `jpg`, or `png`. |
| `-w`, `--weight` | `0.5` | Restoration weight passed to `GFPGANer.enhance`. |

## Bundled Helper Differences

The bundled `scripts/run_inference.py` preserves the core workflow but changes unsafe defaults:

- It requires a local `--model-path` unless `--allow-download` is explicitly provided.
- It defaults to `--no-bg-upsampler`, avoiding Real-ESRGAN dependency/network/device surprises.
- It accepts `--device` so callers can choose `cpu`, `cuda`, or a specific CUDA device.
- It writes the same conceptual output layout: `cropped_faces/`, `restored_faces/`, `cmp/`, and `restored_imgs/` when pasted-back images are available.

## Model Path Behavior

For explicit, reproducible runs, pass `--model-path /path/to/checkpoint.pth`.

If a user wants automatic checkpoint download, first confirm that network access and cache writes are acceptable, then pass `--allow-download`. Without that flag, the helper fails fast with the expected version filename and URL instead of implicitly downloading weights.

## Output Layout

For an unaligned whole image:

```text
<output>/
  cropped_faces/<basename>_00.png
  restored_faces/<basename>_00.png
  cmp/<basename>_00.png
  restored_imgs/<basename>.<ext>
```

For `--aligned`, no pasted-back image is produced by `GFPGANer.enhance(..., paste_back=False)` unless a wrapper explicitly changes that behavior. The restored face is still saved under `restored_faces/`.

## API Equivalent

```python
import cv2
from gfpgan import GFPGANer

img = cv2.imread("input.jpg", cv2.IMREAD_COLOR)
restorer = GFPGANer(
    model_path="GFPGANv1.4.pth",
    upscale=2,
    arch="clean",
    channel_multiplier=2,
    bg_upsampler=None,
)
cropped_faces, restored_faces, restored_img = restorer.enhance(
    img,
    has_aligned=False,
    only_center_face=False,
    paste_back=True,
    weight=0.5,
)
```
