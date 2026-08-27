# Feature post-processing API reference

Prefer the installed `rs` commands for routine workflows. Use these APIs for smoke tests, custom handlers, debugging, or synthetic cases where a CLI command would require too much fixture setup.

## Probability soft voting

### `robosat.tools.masks.softvote(probs, axis=0, weights=None)`

Purpose: combine one or more class-probability arrays and return the class-index mask from the weighted-average probabilities.

Expected shapes for RoboSat post-processing:

- Each probability array is shaped `(classes, height, width)`.
- For the bundled binary PNG workflow, `classes == 2` after reconstructing background and foreground.
- `probs` is normally a Python list or array stack over model runs.
- With the default `axis=0`, RoboSat averages over model runs and then takes `argmax` over the class axis.

Equivalent logic:

```python
mask = numpy.argmax(numpy.average(probs, axis=0, weights=weights), axis=0)
```

Constraints:

- `weights` must be `None` or have one value per probability input.
- The helper does not validate that probabilities sum to one; the CLI reconstructs binary background from foreground and assumes the binary pair sums to one.
- The result is a numeric class-index array, not a palette image. The CLI wraps it as a `P`-mode PNG with a two-color palette.

Bundled smoke:

```bash
python sub-skills/feature-postprocessing/scripts/softvote_smoke.py --show-arrays
```

## Feature morphology and contour helpers

These helpers operate on binary NumPy masks and OpenCV contours.

| Helper | Purpose | Key constraints |
| --- | --- | --- |
| `visualize(mask, path)` | Save a binary mask as a palette PNG for visual inspection. | Writes black/white palette values; not the same orange/denim palette used by `rs masks`. |
| `contours_to_mask(contours, shape)` | Rasterize OpenCV contours into a binary mask. | `shape` is the output array shape; contours must use OpenCV contour format. |
| `denoise(mask, eps)` | Morphological opening with an elliptical kernel. | `eps` is kernel size in pixels; too high removes small true positives. |
| `grow(mask, eps)` | Morphological closing with an elliptical kernel. | `eps` is kernel size in pixels; too high can connect distinct objects. |
| `contours(mask)` | Find contour polygons and hierarchy using `RETR_TREE`. | OpenCV return conventions can vary by version; RoboSat expects contours plus hierarchy. |
| `simplify(polygon, eps)` | Simplify an OpenCV polygon with `approxPolyDP`. | `eps` is a fraction in `[0, 1]` of contour arc length. |
| `featurize(tile, polygon, shape)` | Convert tile pixel polygon points to closed WGS84 lon/lat coordinates. | `tile` is a mercantile tile; y is flipped from image coordinates to geographic coordinates. |
| `parents_in_hierarchy(node, tree)` | Walk contour hierarchy ancestors for polygon-hole reconstruction. | Used to attach one level of inner rings to an outer polygon. |

Minimal custom contour flow:

```python
from robosat.features.core import denoise, grow, contours, simplify, featurize

clean = grow(denoise(binary_mask, eps=20), eps=20)
raw_contours, hierarchy = contours(clean)
polygons = [simplify(contour, eps=0.01) for contour in raw_contours]
rings = [featurize(tile, polygons[0], binary_mask.shape[:2])]
```

## Parking feature handler

### `robosat.features.parking.ParkingHandler`

Purpose: turn binary parking masks into GeoJSON polygon features.

Important attributes:

| Attribute | Value | Meaning |
| --- | --- | --- |
| `kernel_size_denoise` | `20` | Opening kernel size in pixels. |
| `kernel_size_grow` | `20` | Closing kernel size in pixels. |
| `simplify_threshold` | `0.01` | Fraction of contour arc length for polygon simplification. |

Methods:

| Method | Behavior |
| --- | --- |
| `apply(tile, mask)` | Validates `tile.z == 18`, denoises/grows the binary mask, extracts contours, reconstructs one outer ring plus direct inner rings, converts pixels to WGS84, skips invalid polygons, and appends features in memory. |
| `save(out)` | Writes accumulated features as a GeoJSON FeatureCollection. |

Usage sketch:

```python
import mercantile
import numpy as np
from robosat.features.parking import ParkingHandler

handler = ParkingHandler()
tile = mercantile.Tile(x=69108, y=105091, z=18)
mask = np.zeros((512, 512), dtype=np.uint8)
mask[100:220, 100:220] = 1
handler.apply(tile, mask)
handler.save("parking.geojson")
```

Constraints:

- The default installed `rs features` command exposes only `--type parking`.
- Thresholds are tuned for z18. Non-z18 tiles raise `NotImplementedError`.
- Very small shapes can disappear after denoise/simplify.
- Deeply nested rings are skipped because the handler only handles one level of holes.
- Invalid Shapely polygons are skipped with warnings.

## Spatial helpers

Module: `robosat.spatial.core`.

| Helper | Purpose | Notes |
| --- | --- | --- |
| `project(shape, source, target)` | Project a Shapely geometry between CRS identifiers. | Uses `pyproj.Transformer.from_crs`. |
| `project_ea(shape)` | Project WGS84 geometry to an equal-area CRS for area/IoU. | Depends on projection data containing `ESRI:54009`. |
| `project_wgs_el(shape)` | Project WGS84 geometry to ellipsoidal Mercator. | Used for buffering by meters in merge. |
| `project_el_wgs(shape)` | Project ellipsoidal Mercator back to WGS84. | Used after buffering/unbuffering. |
| `union(shapes)` | Reduce a non-empty shape list with Shapely union. | Asserts the input list is not empty. |
| `iou(lhs, rhs)` | Intersection-over-union in equal-area projected space. | Returns a value in `[0, 1]`; used by dedupe. |
| `make_index(shapes)` | Build an R-tree index over shape bounds. | Requires `rtree` and the native `libspatialindex` library. |

Merge uses `project_wgs_el` to buffer predicted shapes by `--threshold` meters, builds connected components among intersecting buffered shapes, unions each component, unbuffers by the same threshold, orients polygon exteriors, and computes an integer `area` property with `project_ea`.

Dedupe uses `make_index` to find OSM shapes whose bounding boxes overlap each prediction, unions actual intersections, then keeps a prediction only when `iou(prediction, intersecting_osm_union) < threshold`.

## Graph helper

### `robosat.graph.core.UndirectedGraph`

Purpose: group shapes into connected components for merge.

| Method | Behavior |
| --- | --- |
| `add_edge(s, t)` | Adds both directions of an undirected edge. Merge adds self-edges so isolated shapes become components. |
| `targets(v)` | Returns adjacent vertices. |
| `vertices()` | Returns vertices present in the edge map. |
| `empty()` | Checks whether any edges/vertices exist. |
| `dfs(v)` | Yields vertices reachable from `v`. |
| `components()` | Yields sets of connected vertex ids. |

Use this helper when reimplementing or testing vector cleanup behavior; do not use it as a general graph library for weighted, directed, or vertex-only graphs.
