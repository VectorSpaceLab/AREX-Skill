# Geometry, NMS, matching, and utility contracts

Baseline: StarDist 0.9.2, commit `e80c6de700693bc228ed3c9ba1dc19c3785667ee`.
The source evidence for this reference is the relative package paths
`stardist/geometry/geom2d.py`, `stardist/geometry/geom3d.py`, `stardist/nms.py`,
`stardist/matching.py`, `stardist/sample_patches.py`, `stardist/utils.py`, and
`stardist/plot/`.

## Validation and layout

- Labels are NumPy arrays with integer dtype and values `>= 0`; `0` is
  background. `_check_label_array(y,name,check_sequential=False)` raises
  `ValueError` for wrong dtype/negative values, and can additionally require
  positive IDs `1..max`. `matching` compacts arbitrary positive IDs internally.
- Spatial order is 2D `(Y,X)` / `(row,column)` and 3D `(Z,Y,X)` / `(z,y,x)`.
  A dense grid is sampled at `0,g,2g,...`; each grid value must be a positive
  power of two. `_normalize_grid` rejects the wrong length, non-scalars, and
  non-powers of two.
- Native 2D/3D distance outputs are `float32`. C++/OpenCL output spatial
  lengths are `floor((size-1)/g)+1 == ceil(size/g)`. The Python 3D fallback
  allocates `size//g`, so use it only for divisible shapes or compare it with
  care. Dense NMS points are returned in full-image coordinates after grid
  multiplication.

## Distance and rendering APIs

```python
star_dist(a, n_rays=32, grid=(1,1), mode='cpp')
```

`a` must be a 2D integer label image; `n_rays >= 3`. Returns
`float32 (ceil(Y/gy),ceil(X/gx),n_rays)`, with zero distances at background
sample locations. `mode` is `cpp` (required CPU baseline), `python` (slow
fallback; only `(1,1)` is implemented), or `opencl` (optional `gputools` and
OpenCL). Unknown modes raise `ValueError`.

```python
star_dist3D(lbl, rays, grid=(1,1,1), mode='cpp')
```

The second argument is a `Rays_*` object, not an integer. Its `vertices` have
shape `(R,3)` and its triangular `faces` shape `(F,3)`; `R=len(rays)`. Returns
`float32 (ceil(Z/gz),ceil(Y/gy),ceil(X/gx),R)`. Use the same ray definition for
star distances, NMS, and rendering.

```python
dist_to_coord(dist, points, scale_dist=(1,1))
```

For `dist=(N,R)` and `points=(N,2)`, returns `float32`-like coordinates of
shape `(N,2,R)` in `(row,column)`. `scale_dist` scales the two coordinate
axes. `dist_to_coord3D(dist, points, rays_vertices)` requires `(N,R)`, `(N,3)`,
`(R,3)` and returns `(N,R,3)` in `(z,y,x)`.

```python
polygons_to_label(dist, points, shape, prob=None, thr=-np.inf,
                  scale_dist=(1,1))
polygons_to_label_coord(coord, shape, labels=None)
```

2D distances are `(N,R)`, points `(N,2)`, coordinates `(N,2,R)`, and output is
exact `shape`, dtype `int32`. `polygons_to_label` keeps `prob > thr` (strict),
stably sorts by increasing probability, and gives consecutive IDs in retained
order; later rasterized polygons overwrite earlier ones. The lower-level
`polygons_to_label_coord` writes `label+1` for each supplied `labels` value
(the default offsets are `0..N-1`), so it is not an arbitrary-ID writer.

```python
polyhedron_to_label(dist, points, rays, shape, prob=None, thr=-np.inf,
                    labels=None, mode='full', verbose=True,
                    overlap_label=None)
```

3D `dist` is `(N,R)` (a single vector is reshaped), points `(N,3)`, and
`len(rays)==R`; all distances must be positive. `prob`/`labels` are length N.
Candidates with `prob >= thr` (inclusive) are sorted by decreasing probability.
A non-empty native call returns an exact-shape `int32` image; the empty-point
fast path returns `uint16` zeros. Default labels are `1..N`; explicit labels
are written directly. Modes are `full`, `kernel`, `hull`, `bbox`, and `debug`;
unknown modes raise `KeyError`. `overlap_label` marks multiply covered voxels.

`relabel_image_stardist` and `relabel_image_stardist3D` are round-trip
star-convex diagnostics, not guarantees for concave or clipped objects.
Module-level `dist_to_volume(dist,rays)` expects rank-4 `(...,R)` data and
`dist_to_centroid(dist,rays,mode='absolute')` expects rank 4 and mode
`absolute`/`relative`; they are lower-level helpers, not root exports.

## NMS

```python
non_maximum_suppression(dist, prob, grid=(1,1), b=2, nms_thresh=.5,
                        prob_thresh=.5, use_bbox=True, use_kdtree=True,
                        verbose=False)
```

Dense 2D inputs are `dist=(Ny,Nx,R)`, `prob=(Ny,Nx)`, and shape-aligned.
Candidates satisfy `prob > prob_thresh`; scalar `b` excludes that many sampled
pixels on every edge (or pass per-axis `(before,after)` pairs). Returns
`(points, scores, distances)` with `(K,2)`, `(K,)`, `(K,R)`, sorted by descending
candidate score. Suppression occurs when overlap exceeds `nms_thresh`, where
overlap is intersection divided by the smaller polygon area, not union IoU.

```python
non_maximum_suppression_sparse(dist, prob, points, b=2, nms_thresh=.5,
                               use_bbox=True, use_kdtree=True, verbose=False)
```

Sparse 2D inputs are `(N,R)`, `(N,)`, `(N,2)` and return
`(points_kept, prob_kept, dist_kept, original_indices)`. The fourth array maps
back to the original unsorted input. Sparse `b` is accepted for compatibility
but is not applied as a border mask.

The dense 3D signature is
`non_maximum_suppression_3d(dist, prob, rays, grid=(1,1,1), b=2,
nms_thresh=.5, prob_thresh=.5, use_bbox=True, use_kdtree=True,
use_gravity=True, verbose=False)`. Inputs are `(Nz,Ny,Nx,R)` and `(Nz,Ny,Nx)`;
outputs are `(K,3)`, `(K,)`, `(K,R)`. The sparse 3D signature is
`non_maximum_suppression_3d_sparse(dist,prob,points,rays,b=2,nms_thresh=.5,
use_kdtree=True,use_gravity=True,verbose=False)` with `(N,R)`, `(N,)`, `(N,3)`
and the same four-return contract. `b` is not used by the sparse 3D path.
Low-level `*_inds` wrappers return a Boolean survivor mask and expect aligned
native-compatible arrays.

## Matching and patch utilities

`matching(y_true,y_pred,thresh=.5,criterion='iou',report_matches=False)`
requires equal shapes and integer non-negative labels. Criteria are `iou`
(intersection/union), `iot` (intersection/true), and `iop`
(intersection/pred). The result is a named tuple with `criterion`, `thresh`,
`fp`, `tp`, `fn`, `precision`, `recall`, `accuracy`, `f1`, `n_true`, `n_pred`,
`mean_true_score`, `mean_matched_score`, and `panoptic_quality`. With reporting,
it adds `matched_pairs`, `matched_scores`, and `matched_tps`; pairs below the
threshold remain in `matched_pairs`. A threshold sequence returns a tuple of
results. `matching_dataset`/`matching_dataset_lazy` aggregate images; the
scalar form returns one `DatasetMatching`, `by_image` controls global versus
per-image averaging, and `parallel` uses a thread pool.

`group_matching_labels(ys,thresh=1e-10,criterion='iou')` requires at least two
same-shaped 2D/3D label images, greedily carries IDs across consecutive frames,
does not mutate inputs, and returns an `int32` stack. It is not a global tracker.

`get_valid_inds(img,patch_size,patch_filter=None)` returns one `uint32` vector
per spatial axis, all equal length, for legal patch centers. Each patch size
must satisfy `0 < p <= image_size`; a full-size patch has one center. The filter
must return a same-shape boolean mask. `sample_patches(datas,patch_size,
n_samples,valid_inds=None,verbose=False)` requires equal-shaped data arrays and
returns one array per input, each `(n_samples,*patch_size)`; it samples with
replacement when necessary. `calculate_extents`, `fill_label_holes`,
`edt_prob`, `sample_points`, `grid_divisible_patch_size`, and
`mask_to_categorical` are utility APIs; see the troubleshooting and evaluation
references for edge behavior and threshold use.
