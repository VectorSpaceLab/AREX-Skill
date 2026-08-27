# Segmentation and Shapes Workflows

This reference condenses the stable segmentation-and-shapes paths in `scikit-image`. Use it for drawing primitives, synthetic masks, morphology cleanup, marker-based segmentation, superpixels, graph merges/cuts, and active contours.

## 1) Draw primitives and synthesize masks

Use `skimage.draw` when you need explicit coordinates or masks for later segmentation.

Common primitives:

- `line`, `line_aa`, `line_nd`
- `polygon`, `polygon_perimeter`, `polygon2mask`
- `disk`, `circle_perimeter`, `circle_perimeter_aa`
- `ellipse`, `ellipse_perimeter`
- `rectangle`, `rectangle_perimeter`
- `bezier_curve`, `_bezier_segment`
- `set_color` for painting coordinates into grayscale or RGB arrays

Typical use cases:

- Build a synthetic ROI mask for watershed markers.
- Draw outlines for unit tests or visualization overlays.
- Paint anti-aliased primitives into an existing image.

```python
import numpy as np
from skimage.draw import disk, polygon2mask, random_shapes, set_color

image, labels = random_shapes(
    (128, 128),
    max_shapes=5,
    min_shapes=2,
    allow_overlap=True,
    rng=0,
    channel_axis=None,
)

triangle = np.array([[20, 20], [80, 25], [45, 90]])
mask = polygon2mask(image.shape, triangle)
rr, cc = disk((64, 64), 20)
set_color(image, (rr, cc), 0)
```

`random_shapes` notes:

- Returns `(image, labels)` where `labels` is a list of `(kind, bbox)` tuples.
- The canvas starts as white background (`255`) and shapes are painted on top.
- Use `channel_axis=None` for grayscale output; otherwise the channel axis is inserted at the requested position.
- Keep `intensity_range` inside `0..255`.
- `allow_overlap=False` is the default and is useful when shapes should remain separable.
- If a requested shape does not fit, the function may return fewer shapes and emit a warning.

## 2) Clean and prepare masks with morphology

Use `skimage.morphology` to turn rough masks into segmentation-ready regions.

Useful helpers:

- Binary cleanup: `binary_opening`, `binary_closing`, `binary_erosion`, `binary_dilation`
- Size cleanup: `remove_small_objects`, `remove_small_holes`
- Flooding: `flood`, `flood_fill`
- Skeletons: `skeletonize`, `thin`, `medial_axis`
- Marker prep: `local_minima`, `local_maxima`, `h_minima`, `h_maxima`
- Labeling and shape helpers: `label`, `reconstruction`, `convex_hull_image`, `convex_hull_object`

```python
from skimage import morphology

clean = morphology.remove_small_objects(mask, min_size=64)
clean = morphology.remove_small_holes(clean, area_threshold=64)
clean = morphology.binary_closing(clean, morphology.disk(3))
```

Rules of thumb:

- Use boolean masks for binary morphology.
- Label first if you need to clean disconnected components independently.
- Use `skeletonize` or `thin` when you need a 1-pixel centerline for downstream graph or topology work.
- Use `flood` when you want a binary mask; use `flood_fill` when you want a filled image.
- `flood` and `flood_fill` operate on scalar images; pick a single channel or scalar transform for color images.

## 3) Marker-based watershed

Watershed is the default choice for separating touching objects or labels seeded from markers.

Common patterns:

- Gradient-based watershed for real images.
- Distance-based watershed for touching blobs.
- Compact watershed when you want more regular superpixels or segments.

```python
import numpy as np
from scipy import ndimage as ndi
from skimage import filters, segmentation, morphology

# Binary object separation
binary = morphology.remove_small_holes(mask, area_threshold=32)
distance = ndi.distance_transform_edt(binary)
markers = ndi.label(distance > 0.6 * distance.max())[0]
labels = segmentation.watershed(-distance, markers, mask=binary)

# Gradient-based watershed
markers = np.zeros_like(image, dtype=int)
markers[image < 30] = 1
markers[image > 150] = 2
edges = filters.sobel(image)
labels = segmentation.watershed(edges, markers, compactness=0.01)
```

Watershed notes:

- Markers are integer seeds, not probabilities.
- `mask=` limits the flooded area.
- `compactness > 0` favors more regular regions.
- If a contour-fill approach fails, switch to marker-based watershed or clean the boundary first.
- Use `clear_border` after watershed if border-touching regions should be removed.

## 4) Superpixels and SLIC

Use `slic` when you need a controllable oversegmentation before graph merging or object-level analysis.

Recommended settings:

- `channel_axis=-1` for multichannel images, or `channel_axis=None` for grayscale.
- `start_label=0` when you want zero-based labels, otherwise `1` is often convenient.
- `compactness` trades color similarity against spatial regularity.
- `mask=` computes SLIC only inside a region of interest.
- `spacing=` helps with anisotropic pixels or voxels.
- `enforce_connectivity=True` is usually the safe default.

```python
from skimage import segmentation

labels = segmentation.slic(
    image,
    n_segments=300,
    compactness=10,
    sigma=1,
    start_label=1,
    channel_axis=-1,
)
```

Mask-based superpixels:

```python
roi_labels = segmentation.slic(
    image,
    n_segments=150,
    mask=roi_mask,
    start_label=1,
    channel_axis=-1,
)
```

SLIC notes:

- RGB-like images can be converted to Lab automatically when appropriate.
- Grayscale images must use `channel_axis=None`.
- `relabel_sequential` is useful after downstream graph cuts or manual edits.
- For visualization, pair SLIC with `mark_boundaries` or `label2rgb`.

### 4b) Alternative oversegmentation methods

Use `felzenszwalb` when you want graph-based region merging from local similarity.
Use `quickshift` when you want a mode-seeking superpixel path with reproducible RNG.

```python
from skimage import segmentation

fz = segmentation.felzenszwalb(image, scale=100, sigma=0.8, min_size=20, channel_axis=-1)
qs = segmentation.quickshift(image, ratio=1.0, kernel_size=5, max_dist=10, rng=0, channel_axis=-1)
```

Notes:
- `felzenszwalb` is sensitive to `scale`, `sigma`, and `min_size`.
- `quickshift` is sensitive to `ratio`, `kernel_size`, `max_dist`, and whether `convert2lab` stays enabled.
- Use `find_boundaries` or `mark_boundaries` to inspect the result before graph merging.

## 5) Random walker segmentation

Use `random_walker` when marker-based diffusion should respect local gradients.

Core parameters:

- `beta`: larger values make diffusion less likely across strong edges.
- `mode`: `bf`, `cg`, `cg_j`, or `cg_mg`.
- `return_full_prob=True` returns per-label probabilities instead of a single label map.
- `channel_axis` supports multichannel images.
- `spacing` supports anisotropic data.

```python
import numpy as np
from skimage import segmentation

markers = np.zeros(image.shape[:2], dtype=np.int32)
markers[image < 0.1] = 1
markers[image > 0.9] = 2
labels = segmentation.random_walker(
    image,
    markers,
    beta=10,
    mode='bf',
    channel_axis=None,
)
```

Random walker notes:

- Positive labels are seeds.
- Zero labels are unlabeled pixels.
- Negative labels are inactive and excluded from the graph.
- `cg_mg` may require `pyamg`; if it is missing, the implementation may fall back to another conjugate-gradient mode.
- Multichannel inputs should be normalized per channel before segmentation.

## 6) Graph helpers and region merging

Use `skimage.graph` when segmentation should operate on superpixels, RAGs, or path costs.

Important helpers:

- `pixel_graph`, `central_pixel`
- `shortest_path`
- `MCP`, `MCP_Geometric`, `MCP_Connect`, `MCP_Flexible`, `route_through_array`
- `RAG`, `rag_mean_color`, `rag_boundary`, `show_rag`
- `cut_threshold`, `cut_normalized`, `merge_hierarchical`

Typical pattern:

1. Segment into superpixels with SLIC.
2. Build a RAG from the label image.
3. Merge or cut nodes.
4. Relabel sequentially if you need dense IDs.

```python
from skimage import graph, segmentation

labels = segmentation.slic(image, n_segments=200, compactness=10, start_label=1)
rag = graph.rag_mean_color(image, labels)
merged = graph.cut_threshold(labels, rag, thresh=20)
merged, _, _ = segmentation.relabel_sequential(merged)
```

Graph notes:

- `rag_mean_color` uses mean color differences.
- `rag_boundary` uses boundary strength from an edge map.
- `merge_hierarchical` lets you define custom pre-merge and weight callbacks.
- `join_segmentations` is useful when combining alternative label maps.

## 7) Active contours and snakes

Use active contours when you want a curve or level set to evolve onto a target boundary.

Core options:

- `active_contour` for classical snakes on an initialized polyline.
- `chan_vese` for edge-free segmentation on grayscale images.
- `morphological_chan_vese` for a morphological level-set version of Chan-Vese.
- `morphological_geodesic_active_contour` for edge-driven morphology snakes.
- `inverse_gaussian_gradient` as a common edge-preprocessing step.
- `disk_level_set` and `checkerboard_level_set` for convenient initializations.

```python
from skimage import segmentation

init_ls = segmentation.disk_level_set(image.shape, center=(image.shape[0] // 2, image.shape[1] // 2), radius=20)
seg = segmentation.morphological_chan_vese(image, num_iter=35, init_level_set=init_ls)
```

Active contour notes:

- `chan_vese` and `morphological_chan_vese` expect grayscale images.
- `active_contour` expects a polyline of `(row, col)` coordinates.
- `morphological_geodesic_active_contour` usually works best on an edge-enhanced image such as `inverse_gaussian_gradient(image)`.

## 8) Legacy and experimental segmentation

Use these only when matching older notebooks or legacy code:

- `skimage.future.fit_segmenter`
- `skimage.future.predict_segmenter`
- `skimage.future.TrainableSegmenter`
- `skimage.future.manual_polygon_segmentation`
- `skimage.future.manual_lasso_segmentation`

Notes:

- These helpers emit deprecation-style warnings and are not part of the stable `skimage2` route.
- The trainable path expects labeled training pixels and a feature tensor from elsewhere.
- The manual segmentation helpers are interactive and require a GUI backend.
- `maskSLIC` is not a separate public function; use `segmentation.slic(..., mask=...)`.

## 9) Common label postprocessing

Use these after any segmentation method that produces irregular or sparse labels:

- `clear_border` to remove border-connected regions.
- `expand_labels` to grow labels without overlap.
- `join_segmentations` to combine two label maps.
- `relabel_sequential` to compact label IDs.
- `find_boundaries` and `mark_boundaries` to inspect or overlay boundaries.

```python
from skimage import segmentation

labels = segmentation.clear_border(labels)
labels = segmentation.expand_labels(labels, distance=3)
labels, _, _ = segmentation.relabel_sequential(labels)
```
