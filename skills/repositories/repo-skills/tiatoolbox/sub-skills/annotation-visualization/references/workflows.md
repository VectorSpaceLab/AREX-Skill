# Annotation Visualization Workflows

## Convert model outputs into a store-backed overlay

1. Identify output geometry: centroids become Shapely `Point`; contours become `Polygon`; tile/patch predictions usually become rectangular polygons.
2. Normalize each object into `Annotation(geometry, properties)` with JSON-serializable properties.
3. Preserve class information as `type`; preserve confidence or scalar outputs as numeric properties such as `score`.
4. Use `SQLiteStore()` and `append_many(...)` for bulk output.
5. Save as `<slide-basename>.db` in the overlays directory so the viewer can associate it with the matching slide.
6. Plan coloring with `type`, `score`, or `color` depending on whether the user wants class toggles, continuous values, or fixed per-object colors.

## Inspect and filter an existing store

1. Open the data with `SQLiteStore(path)` for `.db` or `StoreClass.from_geojson(path)` for GeoJSON.
2. Inspect `len(store)`, a small sample of `store.items()`, and available property names through `pquery('*', unique=False)` or selected examples.
3. Test geometry bounds with `bquery(...)` before full geometry queries if the dataset is large.
4. Test property filters on a small area first, for example `where='props["type"] == "tumour"'`.
5. Use `pquery('props["type"]')` or `pquery('props["score"]', unique=False)` to confirm color/filter fields exist.

## Convert GeoJSON or `.dat` for faster repeated viewing

1. Load GeoJSON with `SQLiteStore.from_geojson(...)`; use `scale_factor` or `origin` if coordinates are not baseline slide coordinates.
2. Load HoVerNet-style `.dat` through TIAToolbox conversion utilities, then save the result as a `.db`.
3. Flatten nested properties that users need for UI filtering or color mapping.
4. Ensure the output `.db` filename contains the associated slide basename.
5. Keep original `.geojson` or `.dat` as source data, but point visualization users to the `.db` for speed.

## Plan a visualization session

1. Confirm the slide directory and overlay directory or choose a base directory containing `slides/` and `overlays/`.
2. Check that slide and overlay basenames match.
3. Check whether annotations are `.db`, `.geojson`, `.dat`, graph `.json`, or heatmap image overlays.
4. If the environment is local and interactive, use `tiatoolbox visualize --base-path <base>` or `--slides <slides> --overlays <overlays>`.
5. If running headless or remotely, add `--noshow`, choose a free Bokeh port with `--port`, and document the tile-server port forwarding as needed.
6. Avoid launching the viewer during automated checks unless the user explicitly requests it.

## Use `show-wsi` for direct layer inspection

1. Use repeated `--img-input` values to add a base slide and overlays.
2. Provide matching repeated `--name` values when user-facing layer names matter.
3. For annotation-store layers, set `--colour-by <property>` and `--colour-map categorical` or a matplotlib colormap.
4. Use this path for quick one-off inspection, not for managing full slide/overlay folder conventions.

## Build graph overlays

1. Start from node coordinates in baseline slide pixels and feature vectors for each node.
2. Use `SlideGraphConstructor.build(points, features, ...)` when the user wants the SlideGraph-style clustering and Delaunay connectivity.
3. Use `affinity_to_edge_index(...)` when edges already exist as a square affinity or adjacency matrix.
4. Save JSON with `edge_index`, `coordinates`, optional `feats`, and optional `feat_names`.
5. Place the graph JSON in the overlays directory with a filename containing the slide basename.
6. Tell users that graph nodes and edges have independent UI toggles and edges may be hidden by default.

## Registration overlay note

Visualization can compare registered images in dual-window or overlay mode. Keep source/target ordering consistent with how the registration transform was computed. In overlay mode, load the target image first; otherwise transformations may be applied against the wrong image dimensions. Route deeper image metadata and registration-coordinate questions to `../wsi-io/SKILL.md`.
