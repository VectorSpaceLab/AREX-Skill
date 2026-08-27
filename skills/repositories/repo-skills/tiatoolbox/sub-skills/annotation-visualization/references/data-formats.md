# Annotation and Overlay Data Formats

## AnnotationStore format

Use an `AnnotationStore` when overlays are numerous, repeatedly viewed, or queried spatially.

Recommended store properties:

- `type`: categorical object class. The visualization UI treats this specially for type toggles and class colors.
- `score`: numeric confidence or scalar value for filtering and color mapping.
- `color`: per-annotation RGB triple of floats in the range `0..1`; this special property can be used directly for coloring.
- `prob`, `area`, `label`, or model-specific fields: keep values JSON-serializable and use stable names across slides.
- Nested dictionaries and lists can be stored, but simple flat properties are easier to filter and color.

For large annotation counts, write a `.db` with `SQLiteStore` before launching the viewer. GeoJSON and `.dat` inputs can be loaded directly but incur conversion delay because the viewer converts them internally to an annotation store.

## GeoJSON

TIAToolbox expects GeoJSON-like features:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
  },
  "properties": {"type": "tumour", "score": 0.91}
}
```

For many annotations, wrap features in a `FeatureCollection` and convert with `SQLiteStore.from_geojson(...)` or `DictionaryStore.from_geojson(...)`. If coordinates are not in baseline slide pixels, use `scale_factor`, `origin`, or a transform function while importing.

QuPath-style exports can include extra measurement structures. Use a transform function during import to flatten nested measurement lists into direct properties when those values need filtering or coloring.

## HoVerNet-style `.dat`

HoVerNet-style data is a dictionary keyed by nucleus/object id. Each record commonly contains:

```python
{
    nuc_id: {
        "box": [...],
        "centroid": [x, y],
        "contour": [[x0, y0], [x1, y1], ...],
        "prob": 0.98,
        "type": 2,
        # additional JSON-like properties are allowed
    }
}
```

The viewer can load `.dat` files, and TIAToolbox utility conversion can turn them into stores. Prefer converting to `.db` for repeated visualization or large nuclei sets.

## Overlay folder conventions

The visualization UI expects slides and overlays to be paired by basename.

With a base path:

```text
project-view/
  slides/
    case-001.svs
    case-002.svs
  overlays/
    case-001.db
    case-001.geojson
    case-001-heatmap.png
    case-002.dat
    demo-config.json
```

With separate paths, pass both directories:

```bash
tiatoolbox visualize --slides slides --overlays overlays --noshow
```

When a slide is selected, overlay files become available if their filename contains the slide basename without extension. If overlays do not appear, first check basename spelling, extensions, and whether files are in the overlays directory rather than beside the slides.

## Accepted overlay types

- `.db`: preferred persisted `SQLiteStore` annotation overlay.
- `.geojson`: feature or feature-collection annotation overlay, converted internally before display.
- `.dat`: HoVerNet-style instance dictionary, converted internally before display.
- `.jpg` or `.png`: low-resolution heatmap or image overlay. Black RGB pixels may be treated as transparent; single-channel images are colorized.
- Whole-slide image files: can be added as additional image layers, but are usually heavier than annotation or heatmap overlays.
- `.json` graph overlay: dictionary with graph arrays and optional feature metadata.

## Graph overlay JSON

Graph overlays should be saved as JSON-compatible dictionaries. The central keys are:

```python
{
    "edge_index": [[source0, source1, ...], [target0, target1, ...]],
    "coordinates": [[x0, y0], [x1, y1], ...],
    "feats": [[...], [...]],
    "feat_names": ["feature_a", "feature_b"]
}
```

Use baseline slide coordinates for `coordinates`. `edge_index` is a `2 x n_edges` array of node index pairs. Extra node features can drive hover tooltips and node coloring.

## Color and property conventions

- Categorical coloring: use `type`, class labels, or integer class ids with a dictionary/categorical color map.
- Continuous coloring: use a numeric property and a matplotlib colormap; keep values normalized to `0..1` when possible.
- Direct color: set `properties["color"]` to an RGB tuple/list of floats in `0..1` for each annotation.
- Type-specific coloring: keep `type` stable and add another property, such as `score`, `area`, or `explanation`, for color-by-property controls.
- Avoid strings for numeric fields if users need numeric filters such as `props["score"] > 0.5`.
