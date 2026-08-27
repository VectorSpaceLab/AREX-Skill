---
name: object-detection-metrics
description: "Guides legacy Object-Detection-Metrics PASCAL VOC AP/mAP
  evaluation from detection text folders and direct Python API classes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Object-Detection-Metrics

Use this repo skill when the user needs the legacy Object-Detection-Metrics toolkit behavior for PASCAL VOC-style object-detection metrics: AP, mAP, precision/recall curves, text-folder evaluation, or direct use of the `BoundingBox` / `BoundingBoxes` / `Evaluator` classes.

This skill is self-contained for operating guidance. Prefer its bundled helpers and references instead of reopening or running original repository examples or scripts.

## Quick route

| User task | Read next |
|---|---|
| Evaluate `groundtruths/` and `detections/` text folders for VOC AP/mAP | `sub-skills/file-evaluation/SKILL.md` |
| Handle `xywh` versus `xyrb`, absolute versus relative coordinates, or YOLO-like normalized boxes in text files | `sub-skills/file-evaluation/references/file-format.md` |
| Run a noninteractive, safe replacement for the legacy folder-evaluation script | `sub-skills/file-evaluation/scripts/voc_metrics_eval.py` |
| Build `BoundingBox` objects and call `Evaluator.GetPascalVOCMetrics` from Python data | `sub-skills/python-api/SKILL.md` |
| Choose every-point versus 11-point AP, understand duplicate detections, or inspect inclusive IoU behavior | `sub-skills/python-api/references/metric-behavior.md` |
| Check whether a user-provided checkout/copy can import the source-style API | `sub-skills/python-api/scripts/api_metric_smoke.py` or `scripts/check_env.py` |
| Decide whether this skill is stale for a checkout | `references/repo-provenance.md` |
| Understand selected capabilities and non-goals | `references/workflow-map.md` |
| Diagnose install/import/dependency/version problems | `references/troubleshooting.md` |

## Scope and non-goals

This skill covers:

- PASCAL VOC AP/mAP from simple text folders.
- Ground-truth and detection schemas with `xywh` and `xyrb`/`XYX2Y2` coordinates.
- Relative YOLO-like center/size coordinates when a shared image size is available.
- Direct Python API use of the legacy source modules.
- Safe noninteractive metric helpers and smoke checks.

This skill does **not** cover:

- COCO metrics, video/STT-AP metrics, UI workflows, or file formats added by the newer successor toolkit.
- Training or running an object detector.
- General computer-vision model evaluation outside this repository's PASCAL VOC metric implementation.
- Paper distillation or benchmark-survey reproduction.

## Environment model

For folder evaluation, the bundled `file-evaluation` helper is standard-library-only and does not require the original checkout.

For direct source API use, the legacy repository is source-style rather than a pip-installable package. A user working with a checkout or copied source must make the `lib` directory importable and install the source API dependencies used by imports:

```bash
python -m pip install numpy matplotlib opencv-python-headless
python sub-skills/python-api/scripts/api_metric_smoke.py --repo-root /path/to/checkout
```

Use `opencv-python-headless` on servers unless GUI drawing is explicitly needed. Set `MPLBACKEND=Agg` before importing `Evaluator` when plotting in a headless process.

## Minimal validation commands

Check only the generated helpers:

```bash
python scripts/check_env.py
python sub-skills/file-evaluation/scripts/voc_metrics_eval.py --help
python sub-skills/python-api/scripts/api_metric_smoke.py --help
```

Check a user-provided checkout or copied `lib` directory plus API dependencies:

```bash
python scripts/check_env.py --repo-root /path/to/checkout --require-api-deps
python sub-skills/python-api/scripts/api_metric_smoke.py --repo-root /path/to/checkout --case duplicate
```

Run folder AP/mAP with the self-contained helper:

```bash
python sub-skills/file-evaluation/scripts/voc_metrics_eval.py \
  --gt-folder /path/to/groundtruths \
  --det-folder /path/to/detections \
  --threshold 0.5 \
  --output-text voc-results.txt \
  --output-json voc-results.json \
  --pretty
```

## Metric reminders

- Default AP is PASCAL VOC every-point interpolation.
- IoU uses inclusive pixel-area arithmetic: `(right - left + 1) * (bottom - top + 1)`.
- Detections are sorted by confidence within each class.
- Only one detection can match a ground-truth object; duplicate detections become false positives.
- mAP is the mean AP across classes with at least one ground-truth positive.

## Provenance and refresh

Read `references/repo-provenance.md` before using this skill as evidence for a different checkout. Refresh the repo skill if the commit, dirty state, package layout, core source files, CLI flags, or public examples differ from the recorded snapshot.
