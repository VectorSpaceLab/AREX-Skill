# Data-validation troubleshooting

Use these fixes when class lookup or GT/DR intersection checks fail before mAP evaluation.

## Empty ground-truth folder

Symptoms:

- The helper reports `total ground-truth .txt files: 0`.
- Evaluation would have no reference objects for the selected split.

Likely causes:

- Wrong `--gt-dir` path.
- Annotation conversion wrote files somewhere else.
- Files use a non-`.txt` extension or are nested one level deeper.
- The data split genuinely has no labels.

Actions:

1. Confirm the path points at the folder containing one top-level text file per image, not at the dataset root.
2. If files are nested, either pass the exact leaf folder or copy/convert outputs into a flat evaluator input folder.
3. If source annotations are XML, YOLO, JSON, darknet, or keras-yolo3 style, route to the conversion sub-skill.
4. Do not run evaluation until the GT folder has the expected `.txt` files or the user explicitly confirms an empty-label evaluation design.

## Empty detection-results folder

Symptoms:

- The helper reports `total detection-results .txt files: 0`.
- Class lookup finds GT classes but no DR classes.

Likely causes:

- Wrong `--dr-dir` path.
- The detector/export process did not produce text results.
- Detection files were converted to a different folder.
- Files have non-`.txt` extensions or are nested.

Actions:

1. Confirm the DR path is the folder containing one text file per evaluated image.
2. If the detector produced no detections for an image, decide whether the evaluator expects an empty `.txt` file for that image.
3. If DR outputs are still in darknet stdout, darkflow JSON, YOLO, or keras-yolo3 format, route to conversion.
4. Do not repair by moving GT files out just because all DR files are missing; that would hide the actual detector/export failure.

## Different file counts

Symptoms:

- GT and DR totals differ.
- `GT-only files` or `DR-only files` are non-empty.
- Evaluation reports a missing file pair.

Likely causes:

- Some images were labeled but not detected/exported.
- Some detections were generated for images outside the labeled split.
- Conversion reused stale files from a previous run.
- Filenames were normalized differently on GT and DR sides.

Actions:

1. Inspect the listed GT-only and DR-only names.
2. If the extras are genuinely outside the desired evaluation subset, move them to a backup using the explicit repair workflow.
3. If every GT image should be evaluated, create the missing DR files through the detector/export process rather than removing GT files.
4. If missing GT files are the problem, fix the split or labeling source instead of evaluating unlabelled detections.

## Same count but different basenames

Symptoms:

- GT and DR totals match.
- The helper still reports GT-only and DR-only files.
- Example: GT has `0001.txt`, `0002.txt`; DR has `image_0001.txt`, `image_0002.txt`.

Likely causes:

- Prefixes, suffixes, zero-padding, capitalization, or extension casing differ.
- One side uses image filenames while the other uses numeric IDs.
- The wrong data split was selected for one side.

Actions:

1. Do not trust equal counts as readiness.
2. Normalize filenames upstream or through the conversion workflow so matching images have exactly matching `.txt` names.
3. Rerun the helper after renaming or reconverting.
4. Use backup repair only for true extras, not for systematic naming disagreements.

## Non-intersecting basenames

Symptoms:

- Both folders contain `.txt` files.
- `intersecting filenames: 0`.
- The helper refuses `--confirm-move` repair.

Likely causes:

- The GT and DR paths point at unrelated splits or datasets.
- One side includes a prefix/suffix that the other side lacks.
- You selected a parent folder, backup folder, or stale output folder by mistake.

Actions:

1. Stop before moving files; an empty intersection is usually a path or naming error.
2. Print a few filenames from both folders and compare naming schemes.
3. Correct the selected paths or reconvert/rename files so at least some known images intersect.
4. Only rerun explicit move repair after a non-empty intersection proves that the mismatch is partial.

## Class not found in either folder

Symptoms:

- `--class-name CLASS` reports no files for both ground-truth and detection-results.

Likely causes:

- The class name is misspelled or differs in case.
- Conversion mapped class IDs to different names.
- The selected split does not include that class.
- The wrong folders were passed.

Actions:

1. Check the exact class spelling used in a known annotation line.
2. Remember that the helper matches the first whitespace-separated token exactly.
3. If class IDs or names were converted from another format, route to conversion and inspect the class-list mapping.
4. If the class should be absent, do not force evaluator options for it; record that the selected input set has no such class.

## Class found on only one side

Symptoms:

- The target class appears in GT but not DR, or in DR but not GT.

Likely causes:

- A detector missed every instance of a GT class.
- A detector predicted a class absent from the labeled split.
- GT and DR class names use different spellings or mappings.

Actions:

1. Treat this as diagnostic evidence, not automatically as a file-set problem.
2. If labels are mismapped, fix conversion or class names before evaluation.
3. If detections are genuinely absent for that class, continue to evaluation only after the file-set intersection is ready and the user accepts that behavior.

## Unsafe legacy file moves

Symptoms:

- Someone proposes running a helper that immediately moves non-intersecting files from evaluator input folders.
- The user wants to preserve all original files while debugging.

Risk:

- Immediate moves can hide wrong-path errors, empty intersections, stale conversions, or missing detector output.

Actions:

1. Use the bundled `check_map_inputs.py` helper first with no move flags.
2. If repair is appropriate, specify a backup root outside the GT and DR folders.
3. Add `--confirm-move` only after inspecting the dry-run lists.
4. Never delete files as part of this sub-skill's repair workflow.

## Backup target conflict

Symptoms:

- The helper reports that a backup target already exists.

Likely causes:

- A previous repair used the same backup root.
- The backup folder contains manually copied files.

Actions:

1. Inspect the existing backup before retrying.
2. Choose a new timestamped or task-specific backup root.
3. Do not overwrite backup files unless the user has separately confirmed they are obsolete.

## Wrong file naming or path selection

Symptoms:

- Helper warnings mention non-`.txt` files.
- GT and DR paths are identical.
- File lists look like images, JSON, XML, nested folders, or evaluator output files instead of mAP input text files.

Actions:

1. Pass the exact leaf folders containing mAP input text files.
2. Keep GT and DR paths separate.
3. Convert unsupported annotation formats before using this sub-skill.
4. For image files, plots, animation assets, or evaluator outputs, route to evaluation or conversion as appropriate.
