# Evaluation CLI Reference

Use the bundled safe wrapper unless a larger integrated workflow provides another entry point. It is self-contained, accepts explicit paths, and defaults to no plot and no animation.

```bash
python scripts/run_map_evaluation.py --help
```

## Required path flags

| Flag | Required | Meaning |
| --- | --- | --- |
| `--ground-truth-dir DIR` | yes | Folder containing evaluator ground-truth `.txt` files. |
| `--detection-results-dir DIR` | yes | Folder containing evaluator detection-result `.txt` files. |
| `--output-dir DIR` | yes | Folder where `output.txt`, `summary.json`, and optional artifacts are written. |

The wrapper does not change the working directory and does not assume an `input/` or `output/` folder beside the script.

## Output directory flags

| Flag | Meaning |
| --- | --- |
| `--overwrite` | Delete and recreate `--output-dir` if it already contains files. Without this flag, a non-empty output directory is an error. |

Use a fresh output directory for routine comparisons. Use `--overwrite` only when the prior outputs are disposable.

## Metric flags

| Flag | Meaning |
| --- | --- |
| `--min-overlap FLOAT` | Global IoU threshold for classes without an override. Default: `0.5`. Must be `0.0 < FLOAT < 1.0`. |
| `-i CLASS ...`, `--ignore CLASS ...` | Ignore one or more classes before GT counts, detection summaries, AP, and mAP are computed. |
| `--set-class-iou CLASS IOU [CLASS IOU ...]` | Override IoU thresholds for selected evaluated classes. Pairs must be complete; classes must exist after ignore filtering; IoUs must be strictly between `0.0` and `1.0`. |
| `-q`, `--quiet` | Print only the final mAP line and errors. `output.txt` still contains per-class AP, precision, recall, and counts. |

The source-compatible metric flags are `-q/--quiet`, `-i/--ignore`, and `--set-class-iou`. The wrapper adds explicit path flags and `--min-overlap`.

## Plot flags

| Flag | Meaning |
| --- | --- |
| `--plot` | Enable optional PNG plots. Requires `matplotlib`. |
| `-np`, `--no-plot` | Disable plots. This is accepted for source-CLI compatibility and wins if both `--plot` and `--no-plot` are present. |

Plots are off by default. When enabled, the wrapper writes:

- `classes/<class>.png` — per-class precision/recall plots.
- `ground-truth-info.png` — ground-truth object counts by class.
- `detection-results-info.png` — detection counts by class.
- `lamr.png` — log-average miss rate by class.
- `mAP.png` — AP per class with the mAP in the title.

## Animation flags

| Flag | Meaning |
| --- | --- |
| `--animation` | Enable optional annotated detection frames. Requires `opencv-python` and `--images-dir`. |
| `--images-dir DIR` | Folder of images whose basenames match the GT/DR `.txt` ids. Used only with `--animation`. |
| `-na`, `--no-animation` | Disable animation. This is accepted for source-CLI compatibility and wins if both `--animation` and `--no-animation` are present. |

Animation is off by default. When enabled, the wrapper writes annotated frames under `images/detections_one_by_one/` and cumulative annotated images under `images/` inside the output directory. It does not require a GUI display.

## Typical commands

Minimum metric run:

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir data/ground-truth \
  --detection-results-dir data/detection-results \
  --output-dir runs/map-eval-001 \
  --quiet
```

Repeat a run into the same output directory:

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir data/ground-truth \
  --detection-results-dir data/detection-results \
  --output-dir runs/map-eval-001 \
  --overwrite \
  --quiet
```

Ignore a class and override another class's IoU threshold:

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir data/ground-truth \
  --detection-results-dir data/detection-results \
  --output-dir runs/map-eval-custom \
  --ignore background \
  --set-class-iou person 0.7
```

Enable optional plots after installing matplotlib:

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir data/ground-truth \
  --detection-results-dir data/detection-results \
  --output-dir runs/map-eval-plots \
  --plot
```
