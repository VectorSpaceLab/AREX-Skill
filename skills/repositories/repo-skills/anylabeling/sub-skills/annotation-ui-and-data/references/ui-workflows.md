# Annotation UI workflows

This reference covers AnyLabeling's manual annotation workflow and the CLI/config switches that affect saved labels and day-to-day labeling behavior.

## Startup and session flags that affect annotation

The application entry point accepts a positional `filename` that can be an image or label file. The annotation-relevant flags are:

| Flag | Effect |
| --- | --- |
| `--config <path-or-yaml>` | Loads default config, then merges a YAML file or YAML string. Unknown keys are ignored with a warning except recognized `theme` and `ui` additions. |
| `--output`, `-O`, `-o` | If the value ends with `.json`, it is treated as a single output file; otherwise it is an annotation output directory. In auto-save mode a single output file is rejected because auto-save expects per-image files. |
| `--nodata` | Sets `store_data: false`; saved JSON keeps `imageData: null` and depends on `imagePath` resolving to an image. |
| `--autosave` | Sets `auto_save: true`; moving away from a dirty image saves automatically to the inferred label path or output directory. |
| `--nosortlabels` | Sets `sort_labels: false` for the label dialog/list behavior. |
| `--flags` | Comma-separated flag names or a file with one flag per line. These become image-level checkboxes and save under top-level `flags`. |
| `--labelflags` | YAML string or file mapping label regexes to per-shape flag names. Matching labels get default false flags when loaded/created. |
| `--labels` | Comma-separated labels or one label per line from a file. Used as the label list and required for exact validation. Duplicate entries are invalid in config validation. |
| `--validatelabel exact` | Only labels already in the configured label list/unique label list are accepted, except special auto-labeling edit markers. |
| `--keep-prev` | Starts with `keep_prev: true`; when a new image has no label shapes, shapes from the previous image are copied in and the new image is marked dirty. |
| `--epsilon <float>` | Sets vertex/edge hover tolerance on the canvas. Effective hit-testing tolerance is divided by zoom scale. |
| `--reset-config` | Clears persisted Qt settings and exits; it does not rewrite label JSON. |
| `--logger-level` | Sets logging verbosity; useful while diagnosing load/export issues. |
| `--theme` | UI theme only; does not affect label data. |

Default annotation config includes `auto_save: true`, `store_data: false`, `keep_prev: false`, `sort_labels: true`, `validate_label: null`, shape color/point-size settings, dock visibility, and shortcuts for navigation and shape creation. The default user config is saved on first run so later UI toggles can persist selected options.

## Save/load path rules

For an image file `image.ext`, the natural label file is `image.json` next to the image. When an output directory is set, only the label basename is moved there; the image remains in its source location.

When saving:

1. UI `Shape` objects are serialized into JSON dictionaries.
2. Special auto-labeling edit markers are excluded from normal saved labels.
3. `imagePath` is written as a path relative to the label file directory.
4. `imageData` is base64-encoded only when `store_data` is true; otherwise it is `null`.
5. Top-level image flags and `other_data` are written back.

When loading:

1. If the expected label file exists, AnyLabeling loads its `imageData`, or loads `imagePath` relative to the label file when `imageData` is `null`.
2. If no label file exists, AnyLabeling loads image bytes from the selected image path.
3. Existing shapes and flags are loaded into the canvas/list; if `keep_prev` is active and the loaded label has no shapes, previous shapes are appended.
4. Zoom, scroll, brightness, and contrast state may be reused depending on `keep_prev_scale`, `keep_prev_brightness`, and `keep_prev_contrast`.

Common confusion: `--output out_dir` changes where JSON labels are saved and loaded, not where source images are stored. `--output one.json` is a single-label-file workflow and conflicts with auto-save.

## Image list and navigation

- Opening a directory recursively scans supported image formats except SVG and sorts them naturally.
- Drag-and-drop adds supported image files that are not already in the file list.
- Next/previous buttons use the current file list order. Holding Ctrl+Shift while navigating temporarily enables keep-previous-label behavior for that transition.
- The file list checkbox is checked when the corresponding label file exists; with an output directory, existence is checked in that directory.
- Dirty images trigger a save/discard/cancel prompt unless auto-save already saved them.

## Manual shape creation

Supported `shape_type` values are:

- `polygon`
- `rectangle`
- `point`
- `line`
- `circle`
- `linestrip`

Creation behavior:

- Polygon: left-click adds vertices; closing near the first vertex, pressing Return when closable, or double-click close finalizes. The default double-click behavior is `close`.
- Rectangle: first click anchors one corner; second point is the opposite corner. On finalization, the UI normalizes points to top-left then bottom-right.
- Circle and line: first click starts; second point finalizes.
- Point: a single click finalizes immediately.
- Linestrip: left-click adds vertices; Ctrl+left-click finalizes.
- Esc cancels an in-progress shape; Ctrl+Z can undo the last point while drawing.

## Editing canvas behavior

- Hovering near a vertex highlights it. Hovering near an edge of a polygon/linestrip can insert a point.
- Dragging selected shapes and vertices is clamped to the pixmap bounds. Current behavior handles sub-pixel movement and right/bottom edges using the same `w - 1`, `h - 1` boundary as the canvas bounds check.
- Arrow keys move selected shapes by a fixed small offset and apply the same bounded movement.
- Duplicate creates deep copies and shifts them by a small bounded offset; if shifting one way would leave the image, it tries the other way.
- Delete removes selected shapes; Backspace can remove a selected point, deleting the shape if it becomes empty.
- Shape visibility is controlled by the object list checkboxes and affects selection/painting, not the saved JSON data.

## Labels, text, flags, and groups

- Each shape has `label`, optional `text`, `flags`, and `group_id` fields.
- The right-side text editor edits selected shape text when exactly one shape is selected; otherwise it edits image-level text stored under `other_data["image_text"]`.
- Image flags are top-level `flags`; per-shape flags are stored inside each shape.
- `label_flags` regex rules seed per-shape flags when loading/creating labels.
- Grouping selected shapes assigns a shared numeric `group_id`; if selected shapes already include groups, the lowest selected group id is reused and other selected groups are merged. Ungrouping clears all shapes that share the selected group ids.
- Group visualization expects group ids to be integer-compatible. Non-integer group ids may load from JSON but can break group color rendering.

## Exact label validation workflow

Use exact validation when a closed label vocabulary is required:

1. Provide a label list through config or `--labels`.
2. Enable `validate_label: exact` or pass `--validatelabel exact`.
3. Ensure configured labels are unique; duplicate configured labels are rejected.
4. Unknown labels typed in the UI are rejected before they are assigned to a shape.

Exact validation is interactive. Existing JSON files can still contain unknown labels if they were produced elsewhere; validate them with [../scripts/validate_label_json.py](../scripts/validate_label_json.py) before batch export.
