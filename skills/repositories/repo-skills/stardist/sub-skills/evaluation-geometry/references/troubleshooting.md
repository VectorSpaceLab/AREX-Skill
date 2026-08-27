# Geometry and evaluation troubleshooting

## Environment and backend

**Compiled extension import fails.** The CPU baseline requires imports and small
calls through the installed `stardist.lib.stardist2d` and `stardist.lib.stardist3d`.
Repair the Python/NumPy ABI or reinstall the package in the prepared environment;
do not copy private `.so` files or source paths into the runtime skill. Python
mode is a bounded diagnostic fallback, not a substitute for required CPU
verification.

**OpenCL fails.** `mode='opencl'` requires `gputools`, package kernels, a working
OpenCL runtime, and a compatible device. CUDA or TensorFlow GPU visibility does
not prove OpenCL. Use C++ CPU, record OpenCL as `SKIP_NOT_SELECTED` or an
optional-backend block, and never label that skip a CPU pass.

**Python/native grid shapes differ.** Native kernels use indices `0,g,...` and
`ceil(size/g)` output length. The Python 3D implementation allocates
`size//g`; use divisible shapes for fallback parity or make the C++ result the
canonical reference.

## Labels and geometry

**Label validation errors.** Check `isinstance(x,np.ndarray)`, integer dtype,
`x.min() >= 0`, and zero background. Matching accepts arbitrary positive IDs;
3D native geometry casts labels to `uint16`, so keep IDs in a safe range.
`relabel_sequential` can compact IDs and returns `(relabeled,forward,inverse)`.
Do not round floating probabilities into labels.

**2D NMS assertion.** Dense inputs must be `prob=(Ny,Nx)` and `dist=(Ny,Nx,R)`.
Sparse inputs must be `prob=(N,)`, `dist=(N,R)`, `points=(N,2)` and require the
sparse function. Dense NMS outputs full-image points; sparse points are already
full-image. Do not apply grid twice.

**3D shape/ray failure.** `prob.shape == dist.shape[:3]`, `dist.ndim == 4`,
`points.shape[-1] == 3`, and `dist.shape[-1] == len(rays)` must hold. Pass a
`Rays_*` object to `star_dist3D`, not an integer. Reuse the same vertices/faces
for distance generation, NMS, and rendering.

**Grid rejected.** Grid length must equal spatial rank and each value must be a
positive power of two. Use `(1,1)` or `(1,1,1)` as safe defaults. A grid is
sampling metadata, not an arbitrary stride or physical scale.

**Empty/invalid rendering.** Background locations legitimately have zero
star-distance values. 3D candidate distances must all be strictly positive.
If 2D `prob > thr` or 3D `prob >= thr` removes every candidate, rendering
returns background-only data. Check candidate count, output shape, threshold,
and border `b` before lowering a threshold.

## NMS behavior

**Too many/few instances.** Log candidates before/after `prob_thresh`, NMS
survivors, `b`, and `nms_thresh`. Lower probability threshold to admit centers;
raise NMS threshold to retain more overlap. StarDist NMS overlap is intersection
divided by the smaller area/volume, not union IoU. Keep `use_bbox`,
`use_kdtree`, and 3D `use_gravity` fixed when comparing runs.

**Boundary loss with grid.** Dense `b` is applied in sampled tensor coordinates,
so non-unit grids can remove candidates unexpectedly. Border-filter explicitly
when needed. Sparse 2D/3D `b` is accepted for API symmetry but is not applied by
the sparse implementations.

**Sparse candidates lose identity.** The fourth sparse-NMS output is
`original_indices`; use it to map retained arrays back to input order. Do not
assume output row `i` is input row `i` after score sorting.

**Low-level NMS fails on empty data.** Short-circuit zero candidates and return
empty arrays shaped `(0,2)/(0,3)`, `(0,)`, `(0,R)`, and `(0,)` as appropriate.
For non-empty calls, preserve aligned lengths and numeric/contiguous arrays.

## Matching and grouping

**Matching shape/metric surprise.** Ensure equal shapes, non-negative integer
labels, and background zero. Use `report_matches=True` to inspect
`matched_pairs`, `matched_scores`, and `matched_tps`; pairs below threshold
remain in the first two arrays. A threshold sequence returns multiple named
 tuples. Confirm `iou`, `iot`, or `iop` before comparing metrics.

**Grouping drift.** `group_matching_labels` needs at least two same-shaped
images, copies to `int32`, and greedily propagates IDs frame-to-frame. It is not
an identity-global tracker and does not mutate inputs.

## Sampling and plotting

**No patch centers.** Require `0 < patch_size[i] <= img.shape[i]`. A full-size
patch has one legal center. A custom filter must return a same-shape boolean
mask. Sampling with too few centers uses replacement; seed caller RNG for
repeatability.

**RGBA/plot errors.** `render_label` needs a 2D label and a matching 2D/RGB/RGBA
image. `render_label_pred` needs equal-shaped 2D labels. `draw_polygons` needs
`coord=(Ny,Nx,2,R)`, `poly_idx=(N,2)`, and enough colormap entries. In this
0.9.2 snapshot, Matplotlib 3.11.1 removed the `matplotlib.cm.get_cmap` fallback
expected by `render.py`; use a compatible Matplotlib release such as `<3.11` in
an isolated environment or mark plotting optional. Run matching first and keep
overlays separate from quantitative masks.
