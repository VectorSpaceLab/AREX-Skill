# Automatic Mask Generation Workflows

## Run Masks Over a Folder

1. Choose the checkpoint and `--model-type` together: `sam_vit_h_4b8939.pth` with `vit_h` or `default`, `sam_vit_l_0b3195.pth` with `vit_l`, and `sam_vit_b_01ec64.pth` with `vit_b`.
2. Start with the default AMG thresholds and no crop layers.
3. Use `--device cpu` if CUDA is unavailable; use `--device cuda` only when PyTorch can see a compatible GPU.
4. Review each per-image output folder and its `metadata.csv` for mask count, areas, boxes, scores, and crop provenance.

```bash
python sub-skills/automatic-mask-generation/scripts/amg_cli.py \
  --checkpoint sam_vit_b_01ec64.pth \
  --model-type vit_b \
  --input images/ \
  --output masks/ \
  --device cpu
```

## Convert a Folder Run to COCO RLE JSON

PNG output cannot be losslessly converted to the full AMG annotation schema unless the original metadata and masks are preserved. Prefer rerunning AMG with `--convert-to-rle` so the generator returns COCO RLE records directly.

```bash
python sub-skills/automatic-mask-generation/scripts/amg_cli.py \
  --checkpoint sam_vit_b_01ec64.pth \
  --model-type vit_b \
  --input images/ \
  --output masks-rle/ \
  --convert-to-rle \
  --device cpu
```

Before rerunning, check optional dependencies:

```bash
python -c "import cv2; from pycocotools import mask; print('ok')"
```

Use `--overwrite` if the target JSON files already exist and replacement is intended.

## Tune Empty or Sparse Results

If output folders or JSON files contain too few masks:

1. Confirm the image loaded correctly and is not an unsupported/corrupt file.
2. Lower one quality filter at a time, for example `--pred-iou-thresh 0.80` or `--stability-score-thresh 0.90`.
3. Increase sampling with `--points-per-side 48` or `64` if small objects are missed.
4. Add `--crop-n-layers 1` for small objects, then control cost with `--crop-n-points-downscale-factor 2`.
5. Avoid lowering thresholds so far that duplicate or low-quality masks dominate the output.

Example:

```bash
python sub-skills/automatic-mask-generation/scripts/amg_cli.py \
  --checkpoint sam_vit_l_0b3195.pth \
  --model-type vit_l \
  --input image.jpg \
  --output tuned/ \
  --pred-iou-thresh 0.80 \
  --stability-score-thresh 0.90 \
  --points-per-side 48 \
  --device cuda
```

## Avoid GPU OOM

Memory pressure usually comes from large images, `points_per_batch`, high point density, crop layers, and binary mask materialization.

Try these in order:

1. Reduce `--points-per-batch`, for example from `64` to `16` or `8`.
2. Reduce `--points-per-side`, for example from `64` to `32` or `16`.
3. Set `--crop-n-layers 0`, or keep only `1` crop layer with `--crop-n-points-downscale-factor 2`.
4. Use `--convert-to-rle` for large images so returned masks are compact RLE records instead of many full-size boolean arrays.
5. Switch to a smaller model type and matching checkpoint, such as `vit_b`.
6. Use `--device cpu` if correctness matters more than speed and GPU memory is insufficient.

Memory-conservative example:

```bash
python sub-skills/automatic-mask-generation/scripts/amg_cli.py \
  --checkpoint sam_vit_b_01ec64.pth \
  --model-type vit_b \
  --input large.jpg \
  --output large-rle/ \
  --convert-to-rle \
  --points-per-batch 8 \
  --points-per-side 24 \
  --crop-n-layers 0 \
  --device cuda
```

## Use the API in a Pipeline

```python
import cv2
from segment_anything import SamAutomaticMaskGenerator, sam_model_registry

sam = sam_model_registry["vit_b"](checkpoint="sam_vit_b_01ec64.pth")
sam.to(device="cpu")

generator = SamAutomaticMaskGenerator(
    sam,
    points_per_side=32,
    points_per_batch=16,
    pred_iou_thresh=0.86,
    stability_score_thresh=0.92,
    output_mode="coco_rle",
)

image = cv2.cvtColor(cv2.imread("image.jpg"), cv2.COLOR_BGR2RGB)
records = generator.generate(image)
```
