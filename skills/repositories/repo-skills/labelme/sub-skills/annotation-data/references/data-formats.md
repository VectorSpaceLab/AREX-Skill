# Data Formats

## Annotation File structure

A labelme Annotation File is a JSON object. The current codec requires these
keys:

- `shapes`: list of Shapes.
- `imagePath`: original image filename, often relative to the JSON file.
- `imageData`: base64-encoded image bytes or `null`.

The codec also understands these optional keys:

- `version`: labelme version string; `write_label_file` writes it, but the
  current reader does not require it.
- `flags`: image-level Flags, usually a mapping of string to boolean.
- `imageHeight` / `imageWidth`: declared image dimensions, checked when present.

Unknown top-level keys are preserved by the installed codec and should be kept
when they are not reserved. Reserved keys cannot be supplied through
`Annotation.other_data` when writing.

## Shape structure

Each Shape is an object with at least:

- `label`: string Label.
- `points`: non-empty list of `[x, y]` coordinate pairs. The current codec
  requires exactly 1 point for `point`, 2 for `rectangle`, `line`, `circle`,
  and `mask`, and 4 for `oriented_rectangle`. `polygon`, `linestrip`, and
  `points` retain any non-empty point list, including degenerate lists saved by
  the editor.
- `shape_type`: one of `polygon`, `rectangle`, `oriented_rectangle`, `point`,
  `line`, `circle`, `linestrip`, `points`, or `mask`; the current codec requires
  this field rather than defaulting it.

Common optional fields:

- `group_id`: integer or `null`.
- `flags`: per-Shape Flags mapping.
- `description`: free text.
- `mask`: base64-encoded PNG for Mask Shapes.

## Semantic notes

- A Shape is one region on one Image; an Annotation is the whole JSON bundle.
- A Flag is image-level; a Shape Flag belongs to one Shape.
- A Mask Shape carries dense pixel data inside the Shape, not as a separate
  top-level file. Its `points` are `[x, y]` bbox corners; the local mask array
  is indexed `[row=y, column=x]`. For integer corners, the second corner is
  inclusive, so a matching patch is `(y2 - y1 + 1, x2 - x1 + 1)`.
- `group_id` links Shapes that belong together for instance-oriented workflows.
- `imageData` is optional because consumers may load the image from `imagePath`;
  when embedded data is present, the codec uses it instead of reading the path.

## Rasterization behavior

The JSON codec stores Shapes; rasterization is performed by helpers. Keep these
surfaces distinct:

- Non-mask Shapes are rasterized onto the image canvas when building training
  labels.
- The installed `labelme._utils.shape.shape_to_mask` supports polygon,
  rectangle, oriented-rectangle, point, line, circle, and linestrip. It does
  not rasterize the valid `points` Shape type or Mask Shapes; `shapes_to_label`
  handles masks separately.
- `examples/utils.py` is a compatibility reader: it defaults an omitted
  `shape_type` to `polygon`, and its `shape_to_mask` has no `points` branch.
  Do not use that permissiveness to infer current codec requirements.
- The bundled self-contained
  [`shared JSON helper`](../../../scripts/labelme_json_core.py) adds a
  point-marker implementation for `points` and also handles Mask Shape
  placement. Use it for headless conversions instead of assuming internal
  helper parity.
- Canvas drawing clips non-mask geometry to the image extent. Mask placement
  clips the local patch to the canvas while preserving its source offset.
- A Mask Shape's bbox extent may drift from the local mask dimensions after a
  fractional whole-shape drag; the codec loads that file, but an exporter must
  detect and repair the mismatch rather than silently stretch or shift pixels.

## Validation expectations

- `imageHeight` and `imageWidth` must match the decoded image when they are
  present.
- `flags` must map string keys to boolean values.
- `points` must be a non-empty list of finite `[x, y]` pairs, with the
  shape-specific counts listed above for fixed-size Shape types.
- `shape_type` must be present and supported by the installed codec.
- `mask` must decode from base64 PNG only for `shape_type='mask'`.
- Windows-style backslashes in `imagePath` are normalized to forward slashes on
  load.

## Use with bundled tools

- [`scripts/validate_labelme_json.py`](../scripts/validate_labelme_json.py)
  validates and summarizes these structures.
- The [`shared JSON helper`](../../../scripts/labelme_json_core.py) contains the
  self-contained rasterization and parsing logic used by the export helpers.
- If labels are supplied for a downstream consumer, keep the vocabulary in sync
  with the Shape labels present in the JSON file.
