# Cross-cutting troubleshooting

Use this reference for install/import, dependency, staleness, and scope issues that affect more than one Object-Detection-Metrics workflow.

## The repository is not pip-installable

The legacy project has no `pyproject.toml`, `setup.py`, or `setup.cfg`. Do not assume:

```bash
pip install object-detection-metrics
```

For text-folder AP/mAP evaluation, prefer the bundled standard-library helper:

```bash
python sub-skills/file-evaluation/scripts/voc_metrics_eval.py --help
```

For source API use, work with a checkout/copy and add its `lib` directory to `sys.path`; see `sub-skills/python-api/SKILL.md`.

## Source API import fails

Symptoms include:

- `ModuleNotFoundError: BoundingBox`
- `ModuleNotFoundError: BoundingBoxes`
- `ModuleNotFoundError: Evaluator`
- `ModuleNotFoundError: utils`

Recovery:

1. Confirm the user supplied a checkout/copy with a `lib` directory containing the expected source files.
2. Add the `lib` directory itself to `sys.path`, not just the repository root.
3. Run:

   ```bash
   python scripts/check_env.py --repo-root /path/to/checkout --require-api-deps
   python sub-skills/python-api/scripts/api_metric_smoke.py --repo-root /path/to/checkout
   ```

## `cv2` or OpenCV import failure

`utils.py` imports `cv2` when source modules are imported. This can fail even for metric-only API code.

- On servers or CI, install `opencv-python-headless`.
- Install `opencv-python` only when GUI windows are actually required.
- Folder evaluation with `sub-skills/file-evaluation/scripts/voc_metrics_eval.py` avoids OpenCV entirely.

## Matplotlib or display backend errors

`Evaluator.py` imports `matplotlib.pyplot`, and plotting defaults can try to open a display. In headless runs:

```python
import os
os.environ.setdefault("MPLBACKEND", "Agg")
```

Set this before importing `Evaluator`. Use `GetPascalVOCMetrics` for metrics-only work, or `PlotPrecisionRecallCurve(..., showGraphic=False, savePath="existing-directory")` if plots are required.

## Old `requirements.txt` pins conflict with modern Python

The source repository's requirements file pins old packages, including GUI dependencies. For the selected skill workflows, a smaller environment is usually enough:

```bash
python -m pip install numpy matplotlib opencv-python-headless
```

Use full old pins only if the user is deliberately reproducing the original environment and accepts resolver/GUI risk.

## The original high-level script prompts or deletes output

The original folder-evaluation workflow clears the requested save directory after prompting. For unattended or safe runs, use the bundled helper in `sub-skills/file-evaluation/scripts/voc_metrics_eval.py`; it writes only explicit output files and never deletes directories.

## Scores differ from another metric library

Check:

- VOC every-point versus 11-point interpolation.
- Inclusive pixel-area IoU (`+1`) versus half-open/continuous boxes.
- `xywh` versus `xyrb` interpretation.
- Relative center/size conversion and image size.
- Whether duplicate detections are counted as false positives after one GT match.

Use `sub-skills/python-api/references/metric-behavior.md` for implementation semantics.

## COCO, UI, video, or successor-tool requests

This skill intentionally covers the legacy Object-Detection-Metrics PASCAL VOC implementation. If the user asks for COCO metrics, newer UI workflows, additional formats, or video/STT-AP metrics, state that this skill is the wrong source anchor and use a skill/source for the successor toolkit instead.

## Staleness check

Before applying this skill to a different checkout, read `references/repo-provenance.md`. Refresh if core source files, examples, CLI flags, package metadata, or public behavior changed.
