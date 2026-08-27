# Annotation Visualization Troubleshooting

## Store persistence surprises

- `DictionaryStore(':memory:')` and `SQLiteStore(':memory:')` are transient; use a file path and `dump(...)`, `commit()`, or `close()` when results must persist.
- `DictionaryStore` is convenient but not optimized for large spatial queries. Switch to `SQLiteStore` for big overlays, repeated viewer loads, or spatial filtering.
- `SQLiteStore` requires SQLite JSON and RTree support. If creation fails with SQLite compile-option errors, use a Python/SQLite build with those features enabled.
- With `SQLiteStore(auto_commit=False)`, remember to `commit()` before expecting a second process or viewer to see changes.

## Missing or invalid geometry

- `Annotation` requires either a Shapely geometry or WKB bytes.
- Store insertion accepts Shapely `Point`, `LineString`, and `Polygon`; invalid contour lists must be converted to valid Shapely geometries first.
- For model outputs that only have centroids, use `Point([x, y])`; for patch outputs, use rectangular polygons from patch bounds.
- If geometry coordinates came from a downsampled image, scale them back to baseline slide pixels before visualization.

## Invalid DSL filters

- Use `props["field"]` or `props.get("field")` and keep string quoting valid.
- Use `is_none(props["field"])` rather than `props["field"] is None`.
- Use `has_key(props, "field")` or `"field" in props` to guard optional fields.
- Parenthesize compound expressions and prefer explicit comparisons, for example `(props["type"] == "tumour") & (props["score"] > 0.5)`.
- Never pass untrusted user text as a filter expression.

## Large annotation load lag

- Convert `.geojson` and `.dat` overlays to `.db` before repeated viewing.
- Prefer `SQLiteStore.append_many(...)` over many single inserts.
- Keep properties compact and JSON-serializable.
- Use `bquery(...)` or spatial bounds first when inspecting a subset.
- In the viewer, very high `max_scale` or showing all small objects while zoomed out can slow rendering.

## Color property errors

- For categorical colors, use a stable property such as `type` with strings or integers.
- For continuous colormaps, use numeric values and normalize to `0..1` where possible.
- For direct object colors, use a `color` property containing RGB floats in `0..1`, not `0..255` integers unless explicitly converted.
- If a property mixes strings, numbers, missing values, and lists, split or normalize it before using it as `colour-by` or the UI color property.

## Overlays do not appear

- Confirm the overlay file is in the overlays directory selected by `--overlays` or under `<base>/overlays` when using `--base-path`.
- Confirm the overlay filename contains the selected slide basename without extension.
- Confirm the extension is supported: `.db`, `.geojson`, `.dat`, `.json`, `.jpg`, or `.png` depending on overlay type.
- Confirm coordinates are in the same slide coordinate system; an overlay may load but appear off-screen if coordinates are scaled or shifted.
- For graph overlays, confirm `coordinates` length matches node count and `edge_index` indexes valid nodes.

## Port conflicts and remote viewing

- `tiatoolbox visualize` starts a Bokeh server, defaulting to port `5006`, and a tile server, defaulting to port `5000`.
- If the Bokeh port is busy, pass `--port <free-port>`.
- If the tile-server port is busy, set the environment variable `TIATOOLBOX_TILESERVER_PORT` to a free port before launching.
- For SSH remote viewing, forward both ports, for example Bokeh and tile-server ports, then open the forwarded Bokeh port in the local browser.
- Use `--noshow` on remote or headless hosts to avoid browser launch attempts.

## Registration overlay ordering

- Keep source and target image ordering consistent with the transform that produced the registration matrix.
- In overlay mode, load the target image first so transform dimensions are interpreted correctly.
- If an overlay appears shifted, mirrored, or scaled incorrectly, check image ordering, coordinate resolution, and metadata through the WSI I/O guidance at `../wsi-io/SKILL.md`.
