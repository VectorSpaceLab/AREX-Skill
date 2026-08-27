# Annotation and Visualization API Reference

## Core objects

- `Annotation(geometry=None, properties=None, wkb=None)` represents one Shapely geometry plus a JSON-like property dictionary. It must be created with either a geometry or WKB bytes, not both.
- Supported geometry classes for store insertion are Shapely `Point`, `LineString`, and `Polygon`.
- Useful methods include `annotation.geometry`, `annotation.wkb`, `annotation.coords`, `annotation.to_feature()`, `annotation.to_geojson()`, `annotation.to_wkb()`, and `annotation.to_wkt()`.
- Properties should remain JSON-serializable if the annotation will be saved, served, filtered through SQL, or converted to GeoJSON.

## Store classes

- `AnnotationStore` is an abstract mapping-like base; instantiate a concrete store.
- `SQLiteStore(connection=':memory:', compression='zlib', compression_level=9, auto_commit=True)` is the usual choice for persistent or large overlays. It uses SQLite JSON and RTree support for faster spatial/property queries.
- `DictionaryStore(connection=':memory:')` is a pure-Python store useful for examples, tests, and small transient conversions. Non-memory connections serialize as newline-delimited GeoJSON-like records.
- Both stores support mapping operations such as `store[key]`, `key in store`, `len(store)`, `store.keys()`, `store.items()`, and `del store[key]`.

## Store mutation

- `store.append(annotation, key=None)` inserts one annotation and returns a generated or supplied key.
- `store.append_many(annotations, keys=None)` is preferred for bulk insertion; `keys` must match the annotation count when provided.
- `store.patch(key, geometry=None, properties=None)` updates one annotation. For properties, it merges supplied keys into the existing property dictionary.
- `store.patch_many(keys, geometries=None, properties_iter=None)` updates many annotations and requires at least one of geometries or properties.
- `store.remove(key)` and `store.remove_many(keys)` delete annotations.
- `store.commit()`, `store.dump(path_or_handle)`, and `store.close()` persist changes when the backend supports persistence.

## Query operations

- `store.query(geometry=None, where=None, geometry_predicate='intersects', min_area=None, distance=0)` returns `{key: Annotation}`.
- `geometry` may be `None`, a bounds tuple `(min_x, min_y, max_x, max_y)`, or a Shapely geometry.
- `geometry_predicate` accepts Shapely-style predicates such as `intersects`, `contains`, `within`, `touches`, `overlaps`, and store-specific helpers such as `bbox_intersects` and `centers_within_k`.
- `store.iquery(...)` returns matching keys.
- `store.bquery(geometry=None, where=None)` returns bounding boxes and uses bounding-box intersection rather than full geometry intersection.
- `store.pquery(select, geometry=None, where=None, unique=True, squeeze=True)` extracts property values. Use `select='*'` only with `unique=False`.
- `store.nquery(...)` performs neighborhood searches around annotations and can use distance modes such as polygon, box, or box-center comparisons.

## DSL `where` filters

The `where` string is evaluated as a restricted expression over `props`, with SQL acceleration where possible for `SQLiteStore` and Python fallback behavior for other stores.

Common examples:

```python
props["type"] == "tumour"
props["score"] >= 0.5
"type" in props
has_key(props, "score")
is_not_none(props.get("score"))
regexp("^tum", props["type"])
"mitotic" in props["tags"]
sum(props["probabilities"]) > 0.9
(props["type"] == "tumour") & (props["score"] > 0.5)
```

Important constraints:

- Do not pass untrusted user text as `where`; expression parsing can execute code in the current process.
- Supported operations include property access, arithmetic, comparisons, boolean-style operations, key checks, list indexing, `sum`, list containment, `is_none`, `is_not_none`, and `regexp`.
- Unsupported or fragile forms include imports, arbitrary Python functions, `len(...)`, and `props["key"] is None`; use `is_none(props["key"])` instead.
- In SQL-translated filters, use `&` and `|` carefully with parentheses for compound predicates.
- SQLite builds without math functions may not support every math expression, especially floor division.

## Conversion helpers

- `store.features()` yields GeoJSON-like feature dictionaries.
- `store.to_geodict()` returns a `FeatureCollection` dictionary.
- `store.to_geojson(path_or_handle=None)` writes or returns GeoJSON text.
- `SQLiteStore.from_geojson(...)` or `DictionaryStore.from_geojson(...)` creates a store from GeoJSON, with optional `scale_factor`, `origin`, and `transform` arguments.
- `store.add_from_geojson(...)` appends GeoJSON features into an existing store.
- `store.to_ndjson(...)` and `StoreClass.from_ndjson(...)` support newline-delimited feature records with optional keys.
- `StoreClass.from_dataframe(df)` and `store.to_dataframe()` bridge Shapely geometries and tabular properties.
- `store.transform(callable)` rewrites all geometries, useful for shifting from slide coordinates to tile-local coordinates.

## TileServer and viewers

- `TileServer(title, layers, renderer=None)` is a Flask app for Zoomify-style slide and overlay tiles.
- `layers` may be a dict mapping layer names to `WSIReader` objects, image paths, annotation `.db` or `.geojson` paths, HoVerNet-style `.dat` paths, or low-resolution image overlays. A list is accepted and uses generated names with the first item as the base slide.
- Annotation rendering defaults to an `AnnotationRenderer` configured around a score/type property; pass a renderer when a task needs a specific `score_prop`, mapper, thickness, or color behavior.
- Do not instantiate and run a server in scripts unless the user explicitly requested an interactive viewer; prefer building a command plan or validating data layout first.

## CLI entry points

- `tiatoolbox visualize --base-path <base>` expects `<base>/slides` and `<base>/overlays`.
- `tiatoolbox visualize --slides <slides_dir> --overlays <overlays_dir> --port <port> --noshow` starts the Bokeh visualization UI and internal tile server while suppressing browser launch.
- `tiatoolbox show-wsi --img-input <path> --name <layer-name>` can be repeated for multiple layers. Use `--colour-by <property>` with `--colour-map <matplotlib-name-or-categorical>` for annotation-store layers.
- Use the CLI/configuration sub-skill for complete option tables.

## Graph utilities

- `delaunay_adjacency(points, dthresh)` builds an adjacency matrix from coordinates with a distance threshold.
- `affinity_to_edge_index(affinity_matrix, threshold=0.5)` converts a square affinity matrix to a `2 x n_edges` edge index.
- `edge_index_to_triangles(edge_index)` converts edges into triangle simplices when possible.
- `SlideGraphConstructor.build(points, features, ...)` clusters point features into graph nodes and returns a graph dictionary with `x`, `edge_index`, and `coordinates`.
- `SlideGraphConstructor.visualise(graph, color=None, node_size=25, edge_color=(0, 0, 0, 0.33), ax=None)` plots nodes and edges, usually over a slide thumbnail.
