# Troubleshooting

Use this page when a media constructor, chart wrapper, or chart helper fails.

## Missing optional dependencies

| Symptom | Likely cause | What to do |
|---|---|---|
| `ImportError` mentioning `swanlab[media]` | `Pillow`, `numpy`, `soundfile`, `moviepy`, or `rdkit` is missing | Install the media extra or skip the rich-media branch. |
| `ImportError` mentioning pyecharts | A chart object or table helper is unavailable | Install pyecharts or fall back to text/scalar logging. |
| `ImportError` mentioning `sklearn` | A `swanlab.plot` helper is being used without scikit-learn | Install scikit-learn or use a direct pyecharts chart instead. |

Notes:

- `moviepy` is part of the optional media bundle, but the current `Video` transformer is GIF-only and does not require moviepy for the lightweight path.
- If `PIL`, `numpy`, or `soundfile` are absent, skip image and audio tests rather than forcing the constructor.
- If `rdkit` is absent, skip molecule conversion and document the dependency gap.

## Path and format failures

### `Html`
- `Html(Path(...))` raises `FileNotFoundError` when the path does not exist or is not a file.
- A plain string ending in `.html` is not automatically a path; if the file does not exist, SwanLab treats it as raw HTML content.
- File-like objects are read from the beginning when possible, so a partially consumed stream is usually still safe.

### `Image`
- A broken or unsupported file path typically raises `ValueError: Failed to open image file: ...`.
- GIF input is rejected.
- Unsupported `file_type` values raise `ValueError` before any file is written.
- If the source object is a NumPy array, the shape must be image-like and the dtype must be compatible with the media path.

### `Audio`
- Raw arrays must be `float32`, `float64`, `int16`, or `int32`.
- The channel count must be one or two.
- One-dimensional arrays are reshaped to mono, so a flat vector is fine.
- When the path branch fails, inspect the underlying `soundfile` error and verify the file is a real audio file.

### `Video`
- Unsupported extensions raise `TypeError` immediately.
- Bad GIF magic raises a second `TypeError` after the file is opened.
- Nonexistent file paths raise `ValueError` from the file-open step.
- If the data is raw bytes or `BytesIO`, make sure the payload is really a GIF.

### `Molecule`
- Invalid SMILES strings raise `ValueError`.
- Unsupported file extensions raise `ValueError`.
- A string that does not look like a supported file path is parsed as SMILES, so a missing file path can fail as a parse error instead of a file error.

### `Object3D`
- Array inputs must be 2D with 3, 4, or 6 columns.
- Dict inputs must include a `points` key.
- Unsupported file extensions or missing files raise file errors before serialization.

## Unsupported object types

- `ECharts` requires an object with `dump_options()`.
- `Image`, `Audio`, `Video`, `Molecule`, and `Object3D` all reject unrelated Python objects with explicit type errors.
- If you pass a framework object that SwanLab does not recognize, convert it to a supported media type first.

## Large file or memory pressure

These transformers buffer the full payload before writing the media file.

Use smaller fixtures when possible:

- resize images with `size=...`,
- downsample audio before wrapping,
- trim HTML or text snippets,
- prefer pyecharts charts or table summaries over huge raw payloads,
- avoid loading giant binary blobs if a path-based or summarized version is enough.

## pyecharts object mismatch

If a chart-like object fails with an `Unsupported chart type` error:

1. Check that it is a pyecharts chart or SwanLab `Table`.
2. Verify that `dump_options()` exists and returns JSON-like chart options.
3. Wrap unsupported content in a real pyecharts chart before logging.
