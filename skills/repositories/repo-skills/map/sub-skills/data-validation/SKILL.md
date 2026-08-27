---
name: data-validation
description: "Inspect class membership and ground-truth/detection-result
  file-set intersections for mAP-style inputs with safe report-first repair
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# data-validation

Use this sub-skill when a future agent must decide whether mAP-style ground-truth and detection-result folders are ready for evaluation, find which files contain a class, or safely repair mismatched `.txt` file sets before running metrics.

## Route here for

- Checking that `ground-truth/` and `detection-results/` contain top-level `.txt` files with matching filenames.
- Diagnosing evaluator errors that imply a missing ground-truth or detection-result pair.
- Finding every GT and DR file whose first token on any annotation line equals a requested class name.
- Reporting GT-only and DR-only files before evaluation.
- Moving non-intersecting files into an explicit backup folder after a report-only dry run and explicit confirmation.

## Do not handle here

- Computing AP, mAP, IoU matching, ignored classes, custom IoU thresholds, plots, animations, or evaluator output files: use `../evaluation/SKILL.md`.
- Converting PASCAL VOC XML, YOLO, darkflow JSON, darknet result text, or keras-yolo3 annotations into mAP text files: use `../conversion/SKILL.md`.
- Deep validation of bounding-box coordinates, confidence values, optional `difficult` behavior, or metric semantics beyond the file-set and first-token class checks owned here.

## Evidence-backed assumptions

- The evaluator expects one ground-truth `.txt` file and one detection-result `.txt` file per image, with matching filenames such as `image_1.txt` on both sides.
- Ground-truth lines start with the class name and then contain box coordinates plus optional `difficult`.
- Detection-result lines start with the class name, then confidence and box coordinates.
- The legacy class finder searched both folders for a class by comparing the first whitespace-separated token of each line.
- The legacy intersection helper moved non-intersecting files immediately; this generated skill uses a bundled report-first helper instead.

## First checks

1. Identify the actual GT and DR folders the user wants evaluated. Do not assume implicit repository-relative folders; pass explicit paths to the helper.
2. Run a non-mutating readiness report:

   ```bash
   python sub-skills/data-validation/scripts/check_map_inputs.py \
     --gt-dir /path/to/ground-truth \
     --dr-dir /path/to/detection-results
   ```

3. If the user asks about a class, add `--class-name CLASS` and read both GT and DR results. A class absent from both folders usually means the class label is misspelled, conversion mapped it differently, or the wrong folders were selected.
4. If the report shows GT-only or DR-only files, inspect the listed basenames before moving anything. Same counts can still be invalid when basenames differ.
5. Repair only when the user accepts moving the non-intersecting `.txt` files out of evaluator inputs. Use a backup root outside the GT/DR folders and require explicit confirmation:

   ```bash
   python sub-skills/data-validation/scripts/check_map_inputs.py \
     --gt-dir /path/to/ground-truth \
     --dr-dir /path/to/detection-results \
     --move-extra-to /path/to/map-input-backup \
     --confirm-move
   ```

6. Rerun the report after any repair. Route to evaluation only when the helper reports matching file sets and non-empty intersections.

## Reference map

- Read `references/workflows.md` for step-by-step class lookup, file-set readiness, dry-run interpretation, and explicit backup repair workflows.
- Read `references/troubleshooting.md` for empty folders, same-count/different-basename failures, non-intersecting sets, missing classes, unsafe legacy moves, wrong filenames, and backup conflicts.
- Run `scripts/check_map_inputs.py --help` when you need exact helper options and exit-code behavior.

## Safety rules

- The bundled helper is report-only by default. Supplying `--move-extra-to` without `--confirm-move` prints a plan but still does not move files.
- Never delete GT or DR files as a repair step. The only bundled repair moves non-intersecting `.txt` files to a named backup root.
- Do not move files when the GT/DR intersection is empty; that usually means wrong paths, wrong extensions, or incompatible naming rather than a safe partial mismatch.
- Keep conversion fixes in the conversion sub-skill and metric/debug interpretation in the evaluation sub-skill so this sub-skill stays focused on class lookup and file-set intersection readiness.
