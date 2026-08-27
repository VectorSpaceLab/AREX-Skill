# Segmentation Data and Outputs

## Dataset layout

YOLOv5 segmentation uses a detection-like directory layout plus polygon segment labels. A typical local dataset is:

```text
root/
  images/
    train/*.jpg
    val/*.jpg
  labels/
    train/*.txt
    val/*.txt
```

The data YAML points to the image roots and defines class names. Each label row begins with a class id followed by polygon coordinates normalized to the image dimensions. Detection-only `class x_center y_center width height` labels do not provide segmentation polygons.

## Config/checkpoint pairing

- Use `coco128-seg.yaml` or an equivalent custom segmentation YAML for small smoke checks.
- Use `models/segment/yolov5n-seg.yaml` through `yolov5x-seg.yaml` for scratch model construction.
- Use `yolov5n-seg.pt` through `yolov5x-seg.pt` for pretrained segmentation checkpoints.
- Keep class names and the model head class count aligned.

## Mask options

- `--retina-masks` requests higher-resolution output masks during prediction.
- `--overlap` controls label/target overlap semantics in segmentation training/validation paths.
- Mask downsample settings trade memory/runtime against mask detail.
- Large numbers of masks require careful resizing; the repository contains a regression test for more than 512 mask channels.

## Outputs

Segmentation results combine bounding boxes with masks. Do not parse them as detection-only outputs. When exporting, keep postprocessing and mask shape behavior in mind; a backend may expose raw model tensors rather than the Python result wrapper.

## Validation checklist

1. Confirm image and label roots exist.
2. Confirm every image has the expected label representation.
3. Confirm polygon coordinates are normalized and valid.
4. Confirm class ids are within the `names` range.
5. Confirm the checkpoint is segmentation-specific.
6. Start with a tiny fixture before full COCO segments.
