# mAP repository overview

Cartucho/mAP is a small, script-driven evaluator for object-detection results.
It compares `ground-truth/` and `detection-results/` text files with the same
basename, computes VOC-style AP for each class, and reports mAP as the mean of
those AP values.

## Main workflows

| Workflow | User intent | Bundled owner |
| --- | --- | --- |
| Evaluate AP/mAP | "Compute mAP", "run VOC evaluation", "inspect precision/recall", "apply per-class IoU", "ignore a class" | `sub-skills/evaluation` |
| Convert annotations | "Convert VOC XML", "convert YOLO labels", "convert darkflow JSON", "convert darknet result.txt", "convert keras-yolo3 annotations" | `sub-skills/conversion` |
| Validate inputs | "Find class files", "check missing detection-result files", "repair GT/DR mismatches" | `sub-skills/data-validation` |

## File-layout assumptions

- `ground-truth/` and `detection-results/` each hold one `.txt` file per image.
- Matching images use matching basenames, such as `image_1.txt` on both sides.
- Optional `images/` files are only needed for animation or annotated frames.
- Input rows use whitespace-separated evaluator text, not JSON, XML, or YOLO
  normalized labels.

## Optional dependencies

- `matplotlib` enables PNG plots.
- `opencv-python` enables optional animation and annotated frame generation.
- Neither optional dependency is required for the minimum mAP calculation path.

## Operational order

1. Check GT/DR readiness.
2. Convert any source annotations into evaluator text.
3. Run evaluation with a new output directory.
4. Inspect `output.txt` and `summary.json`.

This order mirrors how the generated sub-skills are organized and keeps the
workflow safe for future agents.
