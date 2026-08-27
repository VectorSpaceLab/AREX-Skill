# Portrait Workflows

Use this reference for U-2-Net portrait drawing, own-image face-crop inference, and portrait/original compositing. The bundled scripts embed the needed model implementation and do not require the original checkout.

## Portrait-set inference

This matches the repository workflow for already split/cropped portrait images:

1. Read top-level images from an input directory.
2. Resize each image to 512x512.
3. Apply RGB normalization equivalent to the source `ToTensorLab(flag=0)` path.
4. Build `U2NET(3,1)` and load `u2net_portrait.pth`.
5. Use `1.0 - fused_output` for portrait-map polarity.
6. Normalize and save one uint8 PNG per input stem.

```bash
python scripts/portrait_infer.py \
  --mode portrait-set \
  --weights PATH_TO_WEIGHTS/u2net_portrait.pth \
  --input-dir INPUT_PORTRAITS \
  --output-dir PORTRAIT_RESULTS \
  --device auto
```

## Own-image face-crop inference

`--mode own-images` adapts the source face-detection demo:

1. Load each image with OpenCV in BGR order.
2. Load the bundled Haar cascade, unless `--cascade` points to another XML file.
3. Detect faces and select the largest face by area.
4. Expand the box, pad at image edges, square-pad the crop, and resize to 512x512.
5. If no face is detected, warn and use the whole image resized to 512x512.
6. Apply the portrait BGR normalization, run `U2NET(3,1)`, invert the fused output, normalize, and save a PNG portrait map.

```bash
python scripts/portrait_infer.py \
  --mode own-images \
  --weights PATH_TO_WEIGHTS/u2net_portrait.pth \
  --input-dir OWN_IMAGES \
  --output-dir YOUR_PORTRAIT_RESULTS \
  --device auto
```

Use own-image mode for photos that are not already normalized head crops. Use portrait-set mode for APDrawingGAN-style split/cropped portrait images.

## Portrait/original composite

The composite workflow blends a blurred RGB original image with the generated portrait map:

```text
composite = gaussian_blur(original, sigma) * alpha + portrait_gray * (1 - alpha)
```

Example:

```bash
python scripts/portrait_composite.py \
  --weights PATH_TO_WEIGHTS/u2net_portrait.pth \
  --input-dir OWN_IMAGES \
  --output-dir COMPOSITES \
  --sigma 20 \
  --alpha 0.5 \
  --device auto
```

`--sigma` must be finite and nonnegative. `--alpha` must be in `[0,1]`. Output filenames are based on the input stem plus `_sigma_<sigma>_alpha_<alpha>_composite.png`; decimal points are written as `p` by the bundled script for portable file names.

## Smoke checks without weights

Use random-weight smoke only to prove runtime plumbing:

```bash
python scripts/portrait_infer.py \
  --mode own-images \
  --input-dir OWN_IMAGES \
  --output-dir SMOKE_PORTRAITS \
  --device cpu \
  --max-images 1 \
  --allow-random-weights-for-smoke
```

The output is not meaningful portrait art. It only verifies dependency imports, bundled model code, preprocessing, forward pass, face-cascade loading, and PNG writing.

## Input-quality checklist

- Head should be close to or larger than 512x512 for best detail.
- Background around the head should be relatively clear.
- Crowded scenes, profile faces, occlusion, low resolution, or strong blur can produce poor portraits even when the script runs.
- When face detection fails, the helper falls back to the whole image and records a warning; consider cropping manually or supplying a better cascade/input.
