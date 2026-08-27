# GFPGAN Inference Workflows

## Purpose

Read this for practical GFPGAN face-restoration workflows using the bundled helper or Python API.

## Workflow 1: Restore One Whole Image

```bash
python sub-skills/inference/scripts/run_inference.py \
  --input photo.jpg \
  --output outputs/gfpgan-photo \
  --model-path weights/GFPGANv1.4.pth \
  --version 1.4 \
  --upscale 2 \
  --no-bg-upsampler
```

Expected behavior:

1. The helper reads `photo.jpg` with OpenCV.
2. GFPGAN detects and crops faces because `--aligned` is not set.
3. The helper saves cropped faces, restored faces, side-by-side comparisons, and a pasted-back restored image when available.
4. It exits non-zero with a clear error if the checkpoint is missing.

## Workflow 2: Restore A Folder

```bash
python sub-skills/inference/scripts/run_inference.py \
  --input input-images/ \
  --output outputs/gfpgan-batch \
  --model-path weights/GFPGANv1.3.pth \
  --version 1.3 \
  --ext auto \
  --suffix restored
```

The helper sorts files in the folder and attempts common image extensions. Use `--ext png` when preserving alpha or avoiding JPEG artifacts matters.

## Workflow 3: Aligned Face Crops

```bash
python sub-skills/inference/scripts/run_inference.py \
  --input aligned-crops/ \
  --output outputs/gfpgan-crops \
  --model-path weights/GFPGANv1.2.pth \
  --version 1.2 \
  --aligned \
  --no-bg-upsampler
```

Use `--aligned` only when each input is already an aligned face crop. Whole photos should not use `--aligned`; leave detection and paste-back enabled.

## Workflow 4: Explicit Python API

```python
from pathlib import Path
import cv2
from gfpgan import GFPGANer

image_path = Path("photo.jpg")
img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
if img is None:
    raise ValueError(f"Could not read image: {image_path}")

restorer = GFPGANer(
    model_path="weights/GFPGANv1.4.pth",
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

Return contract:

- `cropped_faces`: list of detected/aligned 512x512 face crops.
- `restored_faces`: list of restored face arrays, usually 512x512.
- `restored_img`: pasted-back full image when `has_aligned=False` and `paste_back=True`; otherwise `None`.

## Workflow 5: Background Enhancement

Only add Real-ESRGAN when the user asks for non-face/background upsampling:

```bash
python sub-skills/inference/scripts/run_inference.py \
  --input photo.jpg \
  --output outputs/gfpgan-bg \
  --model-path weights/GFPGANv1.4.pth \
  --version 1.4 \
  --bg-upsampler realesrgan \
  --bg-model-path weights/RealESRGAN_x2plus.pth \
  --device cuda
```

If `realesrgan` is not installed or CUDA is unavailable, switch to `--no-bg-upsampler` unless the user explicitly wants to repair the optional dependency path.

## Validation Steps

- Run `python sub-skills/inference/scripts/check_env.py` before loading weights.
- Run `python sub-skills/inference/scripts/run_inference.py --help` to confirm flags.
- For a tiny manual smoke, use one local image and a local checkpoint; do not rely on the original repository sample inputs.

## Output Quality Decisions

- Use `1.3` or `1.4` for most modern restoration tasks.
- Try `1.2` when the user prefers sharper, more stylized outputs.
- Use the original `1` model only when the user asks for paper-model behavior and accepts the extension/JIT setup.
- RestoreFormer is an alternative, not a drop-in explanation for GFPGAN internals.
