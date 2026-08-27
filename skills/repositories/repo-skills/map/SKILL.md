---
name: map
description: "Evaluate detector outputs with VOC-style AP/mAP, convert
  annotations into evaluator text, and inspect or repair GT/DR file sets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# mAP

Use this repo skill for the Cartucho/mAP evaluation workflow: evaluate detector outputs, convert source annotations into the evaluator format, or check whether ground-truth and detection-result folders are ready to run.

## Start here

- If you already have evaluator-ready `.txt` files for `ground-truth/` and `detection-results/`, go to `sub-skills/evaluation/SKILL.md`.
- If you need to convert VOC XML, YOLO, darkflow JSON, darknet `result.txt`, or keras-yolo3 annotations, go to `sub-skills/conversion/SKILL.md`.
- If you need to find classes or check/repair matching filenames before evaluation, go to `sub-skills/data-validation/SKILL.md`.

## Minimum runtime

- Python 3.11 or newer.
- `numpy` for evaluation.
- Optional: `matplotlib` for plots and `opencv-python` for animation.

## Route map

### Evaluation
Read `sub-skills/evaluation/SKILL.md` when the user asks for AP, mAP, precision/recall, IoU thresholds, ignored classes, output interpretation, or optional plots/animation.

Bundled helper:
- `sub-skills/evaluation/scripts/run_map_evaluation.py`

### Conversion
Read `sub-skills/conversion/SKILL.md` when the user needs source annotations or detector outputs transformed into evaluator `.txt` files.

Bundled helper:
- `sub-skills/conversion/scripts/convert_annotations.py`

### Data validation
Read `sub-skills/data-validation/SKILL.md` when the user needs to find a class, compare GT/DR basenames, or safely repair file-set mismatches before evaluation.

Bundled helper:
- `sub-skills/data-validation/scripts/check_map_inputs.py`

## Recommended order

1. Validate the file sets with `data-validation`.
2. Convert any non-evaluator formats with `conversion`.
3. Run AP/mAP with `evaluation`.

That order keeps the workflow explicit and avoids chasing metric errors that are actually data-layout problems.

## What not to do here

- Do not open the original repository checkout as a runtime dependency.
- Do not run the legacy mutating scripts from the source repository; use the bundled helpers in this generated skill tree instead.
- Do not use this root router for metric math details, conversion row schemas, or repair steps. Those belong in the sub-skills and their references.

## References

- `references/repo-overview.md` — quick map of the repo workflows and file-layout assumptions.
- `references/troubleshooting.md` — cross-cutting symptoms that decide whether to route to evaluation, conversion, or data-validation.
- `references/repo-provenance.md` — source commit, branch, dirty-state summary, and evidence paths.
- `references/repo-routing-metadata.json` — structured metadata for the managed repo-skills router.
