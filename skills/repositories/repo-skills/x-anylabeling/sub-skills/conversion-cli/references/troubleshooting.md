# Conversion Troubleshooting

Use this guide when `xanylabeling convert` or `LabelConverter` exits nonzero, produces fewer files than expected, or writes empty output.

## First Checks

1. Confirm the CLI and package version:
   ```bash
   xanylabeling version
   xanylabeling convert
   ```
2. Show task-specific help:
   ```bash
   xanylabeling convert --task <task>
   ```
3. Re-run on a tiny local fixture:
   ```bash
   python scripts/run_conversion_smoke.py --work-dir /tmp/xal-convert-smoke
   ```
4. Use explicit paths for `--images`, `--labels`, and `--output`; avoid relying on defaults while debugging.
5. Remember image and label directory scanning is non-recursive.

## Missing Required Arguments

Typical symptoms:

- `--images is required ...`
- `--labels is required ...`
- `--output is required ...`
- `--classes is required ...`
- `--pose-cfg is required ...`
- `--mapping is required ...`

Fix by matching task requirements in [cli-reference.md](cli-reference.md#registry-summary). Common gotchas:

- `coco2xlabel --labels` expects a COCO JSON file, not a directory.
- `odvg2xlabel --labels` expects an ODVG JSONL file.
- `mot2xlabel --labels` expects a MOT annotation file such as `gt.txt`; `xlabel2mot --labels` expects a directory of XLABEL JSON files.
- `xlabel2vlmr1 --output` expects a JSONL file path, not just a directory.
- YOLO and COCO pose modes require `--pose-cfg`, not `--classes`.

## Wrong `--mode`

The CLI validates mode names for task families:

| Task family | Valid modes |
|---|---|
| YOLO import/export | `detect`, `segment`, `obb`, `pose` |
| VOC import/export | `detect`, `segment` |
| COCO import/export | `detect`, `segment`, `pose` |
| PPOCR import/export | `rec`, `kie` |

Tasks such as DOTA, MASK, MOT, MOTS, ODVG, and VLM-R1-OVD do not use `--mode`.

If using the Python API, note that internal mode names differ for several methods: YOLO detection is `hbb`, YOLO segmentation is `seg`, and VOC/COCO use `rectangle` or `polygon`.

## Classes vs Pose Config

Use `classes.txt` for class-id mappings:

```text
person
car
cat
```

Use pose YAML for keypoints:

```yaml
has_visible: true
classes:
  person: [nose, left_eye, right_eye]
```

Known failures:

- Missing or invalid `classes` mapping in pose YAML raises `ValueError` during `LabelConverter(pose_cfg_file=...)`.
- A pose rectangle label that is not a pose class raises a pose class error during export.
- A pose point label that is not in the configured keypoint list is silently omitted from that instance's keypoint vector unless the rectangle class itself is invalid.

## Pose `group_id` Association Errors

Pose export requires every point and rectangle for one instance to share the same integer-like `group_id`.

Symptoms from verified edge cases:

- `group_id is None ...`: a rectangle or point in pose export has no group id.
- `Invalid group_id ...`: a group id cannot be converted to an integer.
- `Missing rectangle/box_label for pose group_id=...`: a group has keypoints but no rectangle carrying the object class.
- `Unknown box_label '...' ... Expected one of: [...]`: the group's rectangle label is not a configured pose class.

Fix:

1. Group each person/object instance with one rectangle and all its keypoints.
2. Ensure group ids are unique per instance and integer-like.
3. Ensure the rectangle label matches a key under `classes` in the pose YAML.
4. Ensure keypoint point labels match the ordered keypoint names for that class.

For manual XLABEL editing details, route to `../annotation-ui/SKILL.md`.

## OBB / DOTA Out-of-Bounds Skips

The verified converter behavior skips rotated boxes whose points fall outside the image bounds:

- `custom_to_yolo(..., mode="obb", obb_boundary_policy="skip")` skips rotation shapes with any point outside the image.
- `custom_to_dota(...)` also skips out-of-bounds rotation shapes and logs a warning.

Symptoms:

- Conversion succeeds but writes an empty YOLO OBB or DOTA file.
- Output count appears correct but the file has no rows.

Fix:

- Clamp or redraw rotation points within image bounds before export.
- Inspect `imageWidth` and `imageHeight` in the XLABEL file; stale dimensions can make valid-looking points appear out of bounds.
- If using the Python API and you intentionally want to retain out-of-bounds OBBs for nonstandard downstream code, review `custom_to_yolo(..., obb_boundary_policy=...)`. The verified CLI uses the default skip behavior and does not expose that option.

## Mask Mapping Table Problems

Symptoms:

- `--mapping is required` or mapping file not found.
- `Invalid output format specified`.
- Empty or missing polygons from mask import.
- Blank masks on export.

Checklist:

1. Mapping JSON must have `type` and `colors` keys.
2. `type` must be `grayscale` or `rgb`.
3. For `grayscale`, values under `colors` must be integer pixel values.
4. For `rgb`, values must be three-element `[R, G, B]` lists. Invalid RGB color values for individual labels are skipped with warnings.
5. Export only rasterizes XLABEL `polygon` shapes whose labels exist in `colors`; rectangles and unknown labels are ignored.
6. Empty XLABEL shape lists intentionally produce a blank mask rather than failing.

## Missing Images or Labels

Symptoms:

- `Image directory not found`.
- `Label file not found for: ...` warnings.
- Fewer output JSON files than input images.
- No VOC XML files found.

Rules:

- Image scanning accepts common image extensions such as `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tif`, and `.tiff`, with upper-case variants.
- Image scanning is non-recursive.
- Per-image labels are matched by file stem.
- YOLO/DOTA/MASK/VLM-R1 import can default `--labels` to `--images`; this is convenient only when labels live beside images.
- When using `--skip-empty-files` for `xlabel2yolo` or `xlabel2voc`, missing label JSON files are skipped rather than producing empty outputs.

Fix:

- Flatten nested directories or run one conversion per directory.
- Rename labels to match image stems exactly.
- Use explicit `--labels` and `--output` directories to avoid accidental in-place writes.

## `--skip-empty-files` Behavior

Supported only by `xlabel2yolo` and `xlabel2voc`.

- Without `--skip-empty-files`, missing XLABEL JSON can still create empty `.txt` or `.xml` outputs.
- With `--skip-empty-files`, missing labels and empty conversions are not counted/written.
- It does not apply to `xlabel2mask`; blank masks are expected for empty labels.
- It does not apply to COCO, DOTA, MOT, MOTS, ODVG, VLM-R1, or PPOCR exports.

## Unicode Image Paths

The converter uses Unicode-aware image reads for OpenCV paths in relevant export paths. If non-ASCII paths fail on Windows terminals:

```cmd
chcp 65001
```

Also verify:

- The shell passes UTF-8 paths unchanged.
- Python process locale is UTF-8.
- The output directory exists or can be created.

## VOC Missing Geometry Warnings

Verified tests show object-level VOC geometry errors are skipped with warnings rather than failing the whole file.

Examples:

- Object has a name but no `bndbox` or `polygon` for the selected mode.
- `bndbox` exists but a coordinate tag such as `ymax` is missing.
- Polygon has no usable points.

Fix the XML object geometry or accept that the bad object will not be present in the XLABEL output. A missing global `<size>` element is fatal because image dimensions are required.

## Empty Output Files

Empty output can be correct or a sign of filtered data.

Common causes:

- Classes file does not include the XLABEL shape labels, so exporters skip all shapes.
- Requested mode does not match shape types, such as exporting YOLO detect from only polygons or DOTA from rectangles.
- OBB/DOTA points are out of bounds.
- Mask export has no polygon labels present in the mapping file.
- VLM-R1 import answer could not be parsed as JSON-like boxes.
- PPOCR export has no supported text-region shapes or missing `description` values.

Debug approach:

1. Open one input XLABEL JSON and inspect `imageWidth`, `imageHeight`, and `shapes`.
2. Verify labels match `classes.txt`, pose YAML, or mask mapping exactly, including case and spaces.
3. Verify `shape_type` matches the target export mode.
4. Run the equivalent Python API on one file and assert shape counts before and after.

## Headless / Qt Warnings During CLI Use

The `xanylabeling` entry point imports application modules before dispatching conversion commands, so headless hosts may print non-fatal Qt/multimedia warnings. Treat warnings as informational if:

- The process exits with code `0`.
- Expected output files are written.
- The output assertions pass.

Treat as a failure if the command exits nonzero, cannot import PyQt6, or fails before reaching conversion. In that case, fix package installation/runtime first.

## Avoiding Accidental Source Mutation

Conversion commands write outputs and may default `--output` to the image directory for some tasks. For safe operation:

- Always write to a new output directory or file.
- Run the bundled smoke script in a disposable work directory first.
- Do not run conversion directly over an only copy of source labels without a backup.
