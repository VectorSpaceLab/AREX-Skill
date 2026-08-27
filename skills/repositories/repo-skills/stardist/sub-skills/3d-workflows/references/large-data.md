# Large 3D data and memory-safe prediction

There are two different tiling mechanisms. Use the smallest mechanism that
solves the memory problem:

1. `predict_instances(..., n_tiles=...)` keeps one output assembly and splits
   model prediction into overlapping tiles. It is the normal first response to
   a volume that is too large for one forward pass.
2. `predict_instances_big(...)` partitions the full volume into blocks, runs
   full instance prediction per block, removes context and objects not owned by
the block, and writes/concatenates results. It is for volumes too large for the
whole `predict_instances` pipeline and has a strict object-size assumption.

## Tiled `predict_instances`

For a `ZYX` volume, start with a spatial tile tuple such as
`n_tiles=(1,2,2)`; for `ZYXC`, use `(1,2,2,1)`. Every entry is an integer >= 1.
Only `Z`, `Y`, and `X` may be split; `C` must stay 1. Tiling counts follow the
input `axes` argument, not necessarily the physical order of the array before
axis normalization.

```python
labels, details = model.predict_instances(
    img, axes="ZYX", sparse=True,
    n_tiles=(1, 2, 2), show_tile_progress=False,
)
```

The model derives tile overlap from its receptive field, pads the image to
network/grid divisibility, predicts tiles, and crops the padded output. A
spatial tile count of 1 does not mean the volume is split on that axis. If an
axis is omitted from `axes`, the model cannot infer a different order safely.
Use `model._guess_n_tiles(img)` as a starting point for a local model, then
lower the number of simultaneous tiles or use `sparse=True` if memory remains
insufficient. `_guess_n_tiles` is a heuristic, not a guarantee.

Sparse mode is particularly important for large 3D images: it retains only
candidate locations above `prob_thresh`. Dense mode stores a full distance map
with `n_rays` channels and can multiply memory by the ray count. `return_predict`
forces dense mode and should not be used in an OOM recovery path.

Tiling can change edge behavior if overlap is insufficient for the model's
receptive field or if candidate objects cross tile seams. Increase tile overlap
through the model's tile logic where possible, compare against a smaller
reference volume, and use `predict_instances_big` when the full output assembly
itself is the bottleneck.

## `predict_instances_big` contract

Live signature:

```python
model.predict_instances_big(
    img, axes, block_size, min_overlap, context=None,
    labels_out=None, labels_out_dtype=np.int32,
    show_progress=True, **kwargs
)
```

The crucial assumptions are:

```text
all predicted object instances are smaller than min_overlap
min_overlap + 2*context < block_size
```

These inequalities apply per spatial axis. The second is strict (`<`), not
`<=`. If either fails, `Block` construction asserts or an object may cross
multiple write regions and trigger a filtering error. Set `min_overlap` above
the largest expected object extent along each axis, and set `context` at least
as large as the network's receptive-field/tile-overlap requirement. Context is
cropped from the block before labels are written, while overlap is retained to
make one block responsible for each object.

For a volume `img.shape == (Z,Y,X)`, a conservative shape-specific call is:

```python
labels, details = model.predict_instances_big(
    img, axes="ZYX",
    block_size=(64, 128, 128),
    min_overlap=(16, 32, 32),
    context=(16, 32, 32),
    sparse=True, show_progress=False,
)
```

Check before calling:

```python
import numpy as np
block = np.asarray((64, 128, 128))
overlap = np.asarray((16, 32, 32))
context = np.asarray((16, 32, 32))
assert np.all(overlap + 2*context < block)
```

The implementation rounds `block_size`, `min_overlap`, and `context` upward
to the model's axis divisibility/grid. Therefore validate the effective
values printed by the call, not only the requested values. The block cover
also aligns non-final starts/ends to the grid and may increase context to avoid
non-neighboring write-region overlap. Use block sizes large enough to survive
that rounding and to contain the expected object plus context.

### Axes and channel handling

`axes` must contain exactly one label for each `img.ndim`, normally `ZYX` or
`ZYXC`. The output label shape drops `C`, so `labels_out` must have shape
`(Z,Y,X)` and never `(Z,Y,X,C)`. If `C` is present, the method forces a single
block over the full channel dimension and ignores the supplied channel
`block_size`, `min_overlap`, and `context` values by setting them to the image
channel size, 0, and 0. Pass a full channel axis and use channel-safe values to
avoid confusion.

`labels_out=None` allocates a NumPy output using `labels_out_dtype` (default
`int32`). Pass `labels_out=False` when only the details dictionary is needed.
Pass an existing writable array only when its shape exactly equals the output
spatial shape. The returned details concatenate object arrays across blocks;
coordinates are translated into global read-region coordinates and labels are
relabelled with a running offset.

The function overrides several per-block prediction arguments: it forces the
same `axes`, `overlap_label=None`, `return_labels=True`, and
`return_predict=False`; if outer progress is enabled it disables inner tile
progress. Do not expect `overlap_label` or dense raw prediction maps to survive
as a big-inference option. Apply any required post-processing after assembly.

## Choosing block values

1. Measure or conservatively bound object extents in `ZYX` from representative
   labels. Use a per-axis bound, not just the median. `min_overlap` must exceed
   that bound; add margin for noisy predictions.
2. Estimate receptive field with `model._axes_tile_overlap("ZYX")` or use the
   configured model's known tile-overlap requirement. Set `context` at least to
   that estimate for each axis, then check the strict inequality.
3. Select `block_size` to fit one block's image, intermediate distance maps, and
   rendered labels in memory. Larger blocks reduce seam count but increase peak
   memory cubically.
4. Ensure block/context/overlap values are sensible multiples of `grid`. The
   implementation rounds values, but pre-aligning avoids surprising effective
   sizes.
5. Test a small repeated volume where whole-volume and big prediction can both
   run. Compare label matching and `details["points"]`, `dist`, and `prob` after
   lexicographic point sorting.

`tests/test_big.py` demonstrates this equivalence for 3D using a small fixture,
`axes='ZYX'`, `block_size=(55,105,105)`, `min_overlap=(13,25,25)`, and
`context=(17,30,30)`. Treat those values as a bounded test fixture, not a
universal setting for a different model/object scale.

## Recovery matrix

| Symptom | Likely cause | Recovery |
|---|---|---|
| Immediate assertion in block construction | `min_overlap+2*context >= block_size`, negative/invalid values, or block smaller than the volume | Increase block size or reduce overlap/context only after preserving object/receptive-field guarantees; validate per axis. |
| `ValueError` for `labels_out` | Output shape was supplied with channel axis or wrong axis order | Derive `(Z,Y,X)` from `axes` and pass an array with exactly that shape. |
| `RuntimeError` object violates `min_overlap` | An object spans the overlap/responsibility region | Increase `min_overlap`; if it then violates the strict inequality, increase `block_size` or use fewer/larger blocks. |
| Seam duplicates/missing objects | Context too small, object larger than overlap, or invalid axis order | Recheck `axes`, use `context >=` receptive-field overlap, increase `min_overlap`, and compare with whole-volume prediction on a bounded sample. |
| OOM inside a block | One block or dense per-ray map is too large | Reduce block dimensions, keep `sparse=True`, reduce `n_rays`, use CPU/GPU memory intentionally, and avoid `return_predict`. |
| OOM with many tiles | Output assembly or candidate count remains large | Increase spatial tile counts, keep channel tile 1, raise probability threshold only as a deliberate quality tradeoff, and consider big inference with an output target. |
| Block start/end unexpectedly changed | Grid alignment rounded dimensions or distributed excess across strides | Read the effective values printed by the method; choose grid-divisible requested values and retain margin. |

OpenCL/gputools does not remove the block constraints. CUDA may accelerate
TensorFlow but does not guarantee enough memory for dense 3D maps. Optional
accelerator availability must be recorded separately from CPU correctness.
