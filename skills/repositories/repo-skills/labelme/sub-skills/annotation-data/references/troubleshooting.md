# Annotation Data Troubleshooting

## `imageData` is null and the image cannot be found

The JSON stores a path rather than bytes. Resolve `imagePath` relative to the
Annotation File, accounting for Windows separators. When `imageData` is
non-null, the codec decodes the embedded bytes and does not fall back to
`imagePath`; a corrupt embedded payload therefore needs repair rather than a
path-only workaround. If the external image moved, either restore the expected
relative layout or regenerate the Annotation File with embedded image data; do
not silently replace the Image with an empty canvas.

## Dimension mismatch

`imageHeight` and `imageWidth` are declarations checked against decoded image
bytes. Recompute them from the actual Image or remove stale declarations only
when the downstream format allows that loss of metadata. With
`--allow-missing-image-file`, the validator can still check their types but
cannot compare them to the external image until that image is restored.

## Invalid Shape fields

Use [`scripts/validate_labelme_json.py`](../scripts/validate_labelme_json.py) to
identify the first failing Shape. Common fixes:

- Add the missing string `label` and required `shape_type`.
- Ensure `points` is a non-empty list of finite numeric `[x, y]` pairs.
- Use a supported `shape_type` and its required point count: 1 for `point`, 2
  for `rectangle`, `line`, `circle`, and `mask`, and 4 for
  `oriented_rectangle`. The codec intentionally keeps degenerate polygon and
  linestrip lists loadable for round-trip compatibility.
- Keep `mask` only on a Mask Shape and ensure its base64 PNG payload decodes to
  a two-dimensional array.
- Keep `group_id` an integer or `null`; do not use a boolean or string.
- Keep image-level and Shape-level `flags` mappings to string keys and boolean
  values; an empty list or `false` is not a valid substitute for `{}`.

## Unknown labels during rasterization

`shapes_to_label` intentionally fails when a Shape Label is missing from the
provided `label_name_to_value` mapping. Add the Label to the vocabulary rather
than silently assigning an arbitrary class id.

## Mask Shape appears shifted or clipped

A Mask Shape's `points` describe its bbox and its mask is local to that bbox;
points are `[x, y]`, while the array is indexed `[row=y, column=x]`. For an
integer bbox, the second corner is inclusive. Place the local patch into canvas
coordinates using the same source offset, clipping negative or beyond-edge
regions. Do not treat the local mask array as a full-image mask or use a raw
negative NumPy slice, which can wrap pixels onto the opposite edge.

The loader intentionally accepts a mask whose patch dimensions no longer match
the integerized bbox: fractional whole-shape drags can move the bbox without
resampling the stored patch. Before export, compare the patch shape with the
integer bbox extent. Repair the bbox or resample the patch deliberately; do not
silently stretch, crop, or shift the mask to make an assignment fit.

## Downstream code imports old labelme modules

labelme v7 privatized internal modules and has no stable Python API. Prefer the
bundled self-contained helpers or direct JSON parsing. The installed
`labelme._utils.shape.shape_to_mask` also does not handle the valid `points` or
`mask` Shape types; use the bundled
[`shared JSON helper`](../../../scripts/labelme_json_core.py) for headless
rasterization. Pin `labelme<7` only when legacy code truly requires the old
internal API and migration is not yet possible.
