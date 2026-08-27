# Segmentation Troubleshooting

## Detection checkpoint or labels used accidentally

Symptoms include missing masks, shape mismatches, or metrics that only reflect boxes. Use `*-seg.pt` checkpoints and segmentation YAMLs. Detection-only labels are not a segmentation dataset.

## Dataset path or polygon errors

- Validate YAML `path`, `train`, `val`, and `names` before launching.
- Check that every label row has a valid class id and polygon coordinates.
- Check for empty/corrupt labels and images with no corresponding annotation.
- Use `coco128-seg.yaml` or a tiny local fixture to distinguish code errors from dataset-scale issues.

## Memory/runtime issues

- Reduce `--imgsz`, batch size, workers, or mask resolution.
- Avoid `--retina-masks` until the base prediction path works.
- Use CPU only for small checks; CUDA is strongly preferred for training.
- Large mask counts can stress image resizing and memory; preserve the per-mask resize behavior validated by the native test.

## CLI/output issues

- Keep `--project`, `--name`, and `--exist-ok` intentional.
- Use `--nosave` for a parser or minimal runtime check.
- Treat `--overlap` and mask downsample options as semantic choices, not performance-only toggles.

## Hub and export boundaries

PyTorch Hub AutoShape behavior is detection-oriented; do not assume a segmentation model accepts every file/URI/PIL input through the same wrapper. For deployment formats, use the export sub-skill and verify mask output semantics on the target backend.
