# Data-validation workflows

This reference covers only mAP input class lookup and GT/DR file-set intersection checks. Use the evaluation sub-skill for metrics and the conversion sub-skill for changing annotation formats.

## Expected input layout

mAP-style evaluation consumes two sibling concepts:

```text
ground-truth/
  image_1.txt
  image_2.txt

detection-results/
  image_1.txt
  image_2.txt
```

Readiness rules for this sub-skill:

- Each side should contain top-level `.txt` files.
- The filename must match exactly on both sides, including extension and case.
- Matching is by file basename such as `image_1.txt`, not by image contents.
- Ground-truth class lookup reads the first token of lines shaped like `<class_name> <left> <top> <right> <bottom> [difficult]`.
- Detection-result class lookup reads the first token of lines shaped like `<class_name> <confidence> <left> <top> <right> <bottom>`.
- This sub-skill does not validate coordinate geometry, confidence ranges, IoU thresholds, or AP/mAP computation.

## Workflow: report GT/DR readiness

Run the bundled helper with explicit paths:

```bash
python sub-skills/data-validation/scripts/check_map_inputs.py \
  --gt-dir /path/to/ground-truth \
  --dr-dir /path/to/detection-results
```

Read the output as follows:

- `total ground-truth .txt files` and `total detection-results .txt files` should both be non-zero.
- `intersecting filenames` should equal both totals.
- `GT-only files` are ground-truth labels that have no matching detection-result file.
- `DR-only files` are detection-result files that have no matching ground-truth label file.
- `Status: READY` means the top-level `.txt` file sets match and are non-empty.
- `Status: NOT READY` means evaluation is likely to fail or produce misleading results until the named issue is fixed.

A different file count is not the only mismatch. These two folders have the same count but are still invalid:

```text
ground-truth/        detection-results/
  frame_001.txt        frame_002.txt
  frame_003.txt        frame_004.txt
```

The helper explicitly reports this as same count with different basenames.

## Workflow: find files containing a class

Use `--class-name` to adapt the legacy class lookup workflow with explicit GT/DR paths:

```bash
python sub-skills/data-validation/scripts/check_map_inputs.py \
  --gt-dir /path/to/ground-truth \
  --dr-dir /path/to/detection-results \
  --class-name chair
```

Interpretation:

- A file is reported for a side when any non-blank line begins with exactly the requested class token.
- Class matching is exact and case-sensitive. `tvmonitor`, `TVMonitor`, and `tv monitor` are different tokens for this helper.
- If the class appears in GT but not DR, the detector may have produced no detections for that class, or the detection conversion used a different label.
- If the class appears in DR but not GT, detections may be using a label not present in the ground-truth set for the selected data split.
- If the class is absent from both, first suspect a typo, wrong folder, stale conversion, or alternate class spelling before changing evaluation settings.

For large datasets, add `--max-list N` to limit printed filenames. Use `--json-report report.json` when another script or agent needs a machine-readable report.

## Workflow: repair mismatched file sets safely

The legacy intersection helper moved every non-intersecting file into a backup folder immediately. The bundled helper separates inspection from mutation.

1. Run the dry-run report first and inspect all GT-only and DR-only filenames.
2. Confirm that the intersection is non-empty. If it is empty, do not repair by moving; the paths or naming scheme are probably wrong.
3. Choose a backup root outside both evaluator input folders. The helper writes side-specific subfolders under that root:

   ```text
   /path/to/map-input-backup/
     ground-truth/
       gt_only_file.txt
     detection-results/
       dr_only_file.txt
   ```

4. Run with explicit confirmation:

   ```bash
   python sub-skills/data-validation/scripts/check_map_inputs.py \
     --gt-dir /path/to/ground-truth \
     --dr-dir /path/to/detection-results \
     --move-extra-to /path/to/map-input-backup \
     --confirm-move
   ```

5. Rerun the report without move flags. Evaluation can proceed only after remaining GT-only and DR-only lists are empty.

The helper refuses to overwrite existing backup targets. If it reports a backup conflict, choose a new backup root or inspect the existing backup before retrying.

## Workflow: decide whether to repair or report only

Repair is appropriate when:

- The user wants to evaluate only images that have both GT and DR files.
- The missing files are clearly extra examples, stale conversion outputs, or unrelated images.
- The user accepts moving those extras to a recoverable backup location.

Report instead of repairing when:

- The intersection is empty.
- The user might need every GT image evaluated, including false negatives from missing detections.
- Missing detection-result files should be created as empty `.txt` files by the user's detector/export process rather than moved out.
- Missing GT files indicate a labeling or split-selection problem that should be corrected upstream.
- Filenames differ due to extensions, case, prefixes, suffixes, or image IDs that should be normalized by conversion or dataset preparation.

## Legacy workflow mapping

| Legacy behavior | Generated helper behavior |
| --- | --- |
| Search both hard-coded input folders for a class. | `--class-name CLASS` searches explicit `--gt-dir` and `--dr-dir`. |
| Compare GT and DR `.txt` filenames. | Default report compares explicit folder sets without mutation. |
| Move non-intersecting files into `backup_no_matches_found`. | `--move-extra-to BACKUP_ROOT --confirm-move` moves only after an explicit dry-run-compatible plan. |
| Mutate the current checkout based on implicit paths. | Rejects identical GT/DR paths, refuses empty-intersection moves, and requires explicit paths. |

## Handoff after validation

- If file sets match and the user wants AP/mAP, route to `../evaluation/SKILL.md`.
- If files are present but in unsupported annotation formats, route to `../conversion/SKILL.md`.
- If class labels differ between GT and DR, decide whether the issue is spelling/mapping (conversion) or detector behavior (evaluation interpretation) before changing files.
