---
name: evaluation
description: "Run VOC-style AP and mAP evaluation for matching ground-truth and
  detection-result folders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation

Use this sub-skill when the task is to compute VOC-style AP/mAP from already-prepared evaluator text files. It is for metric execution, output interpretation, class filtering, per-class IoU thresholds, and optional visualization artifacts.

## Load When

- The user has a `ground-truth/` folder and a `detection-results/` folder with matching `.txt` basenames.
- The goal is to run AP/mAP, explain AP math, inspect `output.txt`, or compare the effect of `--ignore` / `--set-class-iou`.
- The user asks why an evaluation failed because files are missing, rows are malformed, optional plot/animation dependencies are absent, an output directory would be overwritten, or a class-specific IoU option is invalid.

## Route Elsewhere

- Annotation or detector-output conversion is owned by the sibling `conversion` sub-skill.
- Dataset intersection checks, missing-file repair, and class lookup helpers are owned by the sibling `data-validation` sub-skill.
- This sub-skill may tell the user that those steps are needed, but do not reimplement them here.

## Required Workflow

1. Confirm the two input folders already use evaluator text format and have matching image ids by basename.
2. Read `references/data-formats.md` for row schemas, difficult-object behavior, ignored-class behavior, IoU thresholding, and AP/mAP math.
3. Read `references/cli-reference.md` before invoking the bundled script. Prefer the safe wrapper in `scripts/run_map_evaluation.py`; it requires explicit input/output paths and disables plots/animation by default.
4. Run evaluation with an explicit output directory. Use `--overwrite` only after deciding that deleting the previous output directory is safe.
5. Interpret `output.txt` and `summary.json`; if plots or animation were requested, inspect the generated optional artifacts.
6. If the run fails, use `references/troubleshooting.md` and route conversion or dataset repair requests to the appropriate sibling sub-skill.

## Common Commands

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir path/to/ground-truth \
  --detection-results-dir path/to/detection-results \
  --output-dir path/to/map-output \
  --quiet
```

```bash
python scripts/run_map_evaluation.py \
  --ground-truth-dir path/to/ground-truth \
  --detection-results-dir path/to/detection-results \
  --output-dir path/to/map-output \
  --ignore difficult_class unused_class \
  --set-class-iou person 0.7 car 0.6 \
  --overwrite \
  --quiet
```

## References

- `references/workflows.md` — end-to-end evaluation workflow, output interpretation, optional visualization guidance, and provenance note.
- `references/data-formats.md` — required file layout, GT/DR row schemas, difficult rows, ignore handling, IoU/AP/mAP math.
- `references/cli-reference.md` — bundled wrapper flags and source-compatible flag meanings.
- `references/troubleshooting.md` — recovery for missing files, malformed rows, optional dependencies, output overwrite, IoU override, and ignored-class issues.
