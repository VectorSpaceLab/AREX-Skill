# Conversion Troubleshooting

Use this reference when a conversion command fails or writes unexpected evaluator rows. Keep fixes inside the conversion workflow; route metric failures to `evaluation` and GT/DR file-set repair to `data-validation`.

## Missing or mismatched class lists

Symptoms:

- `class list not found`
- `class list is empty`
- `class id ... is outside class_list range`
- detections/annotations convert to the wrong class names

Likely causes:

- `--class-list` points to the wrong file.
- The class list order does not match the model's zero-based ids.
- Blank lines were inserted and shifted class indices.
- A source row contains a non-integer or out-of-range class id.

Fixes:

1. Confirm the source format uses zero-based class ids.
2. Ensure each class name is one whitespace-free token and appears on exactly one line.
3. Keep the line order identical to the training/inference class order.
4. Re-run the conversion into a fresh output directory or pass `--overwrite` only after inspecting the target directory.

## YOLO image-size lookup failures

Symptoms:

- `YOLO ground-truth conversion needs image dimensions`
- `image not found for YOLO label file ...`
- `could not read dimensions for image ...`
- converted boxes are systematically too large, too small, or shifted

Likely causes:

- YOLO label files are normalized and cannot be converted without image width and height.
- Label stems do not match image stems.
- Images are in nested folders, but `--image-dir` only scans one directory level.
- The image type cannot be read by standard-library probing and Pillow/OpenCV is not installed.
- `--image-size WIDTH HEIGHT` was supplied in the wrong order.

Fixes:

1. Prefer a deterministic size source when possible:
   - use `--image-size WIDTH HEIGHT` for a uniform dataset, or
   - use `--image-size-file` for per-image dimensions.
2. If using `--image-dir`, make image filenames match label stems exactly, for example `frame_001.jpg` for `frame_001.txt`.
3. For nested image trees, generate an `--image-size-file` instead of relying on directory scanning.
4. Install Pillow/OpenCV only if image probing is necessary; the conversion helper itself does not require those packages when dimensions are provided.
5. If images are genuinely missing, stop and report the missing image ids. Do not invent dimensions unless the user provides the correct source size.

## Recursive keras-yolo3 output layout surprises

Symptoms:

- flat output filenames contain `__` separators
- recursive output contains more parent directories than expected
- `image path ... is not under --keras-root ...`
- output files overwrite or collide

Likely causes:

- Default keras-yolo3 conversion flattens image paths to avoid creating nested directories.
- `--recursive` preserves image-path parents under `--output-dir`.
- `--keras-root` was omitted or does not match the image-path prefix in the annotation file.
- Two different image paths collapse to the same flat filename.

Fixes:

1. Use default flat layout for simple one-folder evaluator inputs.
2. Use `--recursive` only when nested output structure is required by the user's later workflow.
3. Add `--keras-root <common-prefix>` to strip dataset roots before writing recursive output.
4. Convert into an empty output directory first. If a collision is intentional, re-run with `--overwrite` only after checking the generated filenames.

## Legacy converter scripts mutate source folders

Symptoms:

- source `.xml`, `.json`, or YOLO `.txt` files disappear into `backup/`
- conversion writes directly into fixed `input/ground-truth` or `input/detection-results` folders
- commands behave differently depending on the current working directory

Likely cause:

- The historical converter scripts were intended for a fixed repository layout and moved source files after conversion.

Fixes:

1. Do not run those one-off scripts for new workflows unless the user explicitly asks for legacy behavior.
2. Use `scripts/convert_annotations.py` from this sub-skill instead.
3. Always pass explicit input and output paths.
4. Keep original annotations/results read-only and write converted `.txt` files into a separate staging directory.

## Invalid annotation rows

Symptoms:

- `expected ... fields`
- `expected ... comma-separated values per bbox`
- `expected a numeric value`
- `label must be a non-empty single token`
- JSON/XML parse errors

Likely causes:

- The selected subcommand does not match the input format.
- Rows contain spaces inside class names.
- Coordinates, confidence, or class id fields contain non-numeric text.
- keras-yolo3 ground-truth rows are being converted with `--dr`, or detection rows are being converted with `--gt`.
- darkflow JSON is not a top-level list of detection objects with the expected keys.

Fixes:

1. Compare the source file with [data-formats.md](data-formats.md).
2. Re-run the helper with the matching subcommand.
3. Fix or remove malformed rows before conversion.
4. Preserve a small failing fixture when reporting the issue so another agent can reproduce the parser error.

## Existing output files

Symptom:

- `refusing to overwrite existing output ...`

Cause:

- The helper defaults to safe writes and will not overwrite existing `.txt` files.

Fixes:

1. Inspect the existing output directory.
2. Delete stale converted outputs, choose a fresh output directory, or add `--overwrite` when replacing them is intentional.

## Unsupported format or task boundary

Symptoms:

- the source is COCO JSON, LabelMe, CVAT XML, a model-specific CSV, or another format not listed in this sub-skill
- the user asks to compute mAP after conversion
- the user asks to move extra GT/DR files into a backup folder

Routing:

- For unsupported annotation formats, either ask for a format specification and write a separate converter outside this sub-skill, or report that the bundled helper does not support it.
- For AP/mAP computation, route to `evaluation`.
- For class lookup, GT/DR basename intersection checks, or non-intersection repair, route to `data-validation`.
