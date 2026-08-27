# AMG CLI Reference

The bundled `scripts/amg_cli.py` is adapted from Segment Anything's automatic mask generation script. It imports heavy dependencies only after argument parsing, so `--help` is safe even when `cv2`, `torch`, or `segment_anything` are not currently importable.

## Basic Commands

Single image to PNG masks and metadata:

```bash
python sub-skills/automatic-mask-generation/scripts/amg_cli.py \
  --checkpoint sam_vit_b_01ec64.pth \
  --model-type vit_b \
  --input image.jpg \
  --output out/ \
  --device cpu
```

Folder of images to COCO RLE JSON files:

```bash
python sub-skills/automatic-mask-generation/scripts/amg_cli.py \
  --checkpoint sam_vit_h_4b8939.pth \
  --model-type vit_h \
  --input images/ \
  --output rle-out/ \
  --convert-to-rle \
  --device cuda
```

## Required Flags

- `--input`: path to one image or to a folder of images.
- `--output`: output directory. The script creates it if needed.
- `--model-type`: one of `default`, `vit_h`, `vit_l`, or `vit_b`.
- `--checkpoint`: path to the matching SAM checkpoint.

## Runtime Flags

- `--device`: PyTorch device, default `cuda`; use `cpu` when CUDA is unavailable or not desired.
- `--convert-to-rle`: write each image's masks as a single COCO RLE JSON file instead of a PNG folder.
- `--overwrite`: allow replacement of an existing per-image PNG output folder or JSON file.

## AMG Flags

- `--points-per-side`: number of sampled points along one image side.
- `--points-per-batch`: number of point prompts processed together.
- `--pred-iou-thresh`: reject masks below this predicted-IoU threshold.
- `--stability-score-thresh`: reject masks below this stability threshold.
- `--stability-score-offset`: amount of mask-threshold perturbation for stability scoring.
- `--box-nms-thresh`: duplicate suppression threshold within a crop.
- `--crop-n-layers`: number of crop layers; `0` means full-image only.
- `--crop-nms-thresh`: duplicate suppression threshold across crop layers.
- `--crop-overlap-ratio`: crop overlap fraction.
- `--crop-n-points-downscale-factor`: downscale point density for deeper crop layers.
- `--min-mask-region-area`: remove holes/islands smaller than this pixel area; requires OpenCV.

Only AMG flags provided on the command line are passed to `SamAutomaticMaskGenerator`; omitted flags use the library defaults.

## Input Handling

For a folder input, the script scans non-directory files with common image extensions: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tif`, `.tiff`, and `.webp`. Unreadable image files are reported and skipped.

## Binary PNG Output Layout

Without `--convert-to-rle`, each input image gets a folder named after the image stem:

```text
out/
  image_a/
    0.png
    1.png
    metadata.csv
  image_b/
    0.png
    metadata.csv
```

Each mask PNG is a single-channel binary image with mask pixels written as `255` and background as `0`.

`metadata.csv` columns:

```text
id,area,bbox_x0,bbox_y0,bbox_w,bbox_h,point_input_x,point_input_y,predicted_iou,stability_score,crop_box_x0,crop_box_y0,crop_box_w,crop_box_h
```

## COCO RLE JSON Output

With `--convert-to-rle`, each input image gets one JSON file named after the image stem:

```text
rle-out/
  image_a.json
  image_b.json
```

The JSON is a list of annotation records. Each record includes `segmentation`, `area`, `bbox`, `predicted_iou`, `point_coords`, `stability_score`, and `crop_box`. The `segmentation` field is COCO RLE and requires `pycocotools` to generate or decode.

## Optional Dependencies

- OpenCV (`cv2`) is required by the bundled CLI for image reading/writing and by `min_mask_region_area > 0` postprocessing.
- `pycocotools` is required for `--convert-to-rle` / `output_mode="coco_rle"`.
