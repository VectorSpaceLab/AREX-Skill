# Large 2D data, tiling, scaling, and block prediction

Tiling limits CNN forward-pass memory. `predict_instances_big` additionally
limits full-image candidate/NMS and label memory. Keep `sparse=True` unless full
maps are needed.

## Select the mechanism

| Problem | Route |
|---|---|
| One forward pass OOMs, but full-image NMS fits | `predict_instances(..., n_tiles=...)` |
| Dense candidate maps/global NMS still OOM | `predict_instances_big(...)` |
| Image resolution differs from model's training scale | `scale=...`, validated on a held-out crop |
| Both activation and global memory are constrained | `predict_instances_big(..., n_tiles=...)` |

For ordinary tiling, use one integer per input axis and never tile channels:

```python
# grayscale YX
labels, details = model.predict_instances(
    img, axes="YX", n_tiles=(4,4), sparse=True,
)
# channel-last YXC
labels, details = model.predict_instances(
    img, axes="YXC", n_tiles=(4,4,1), sparse=True,
)
```

`n_tiles=None` is one full-image tile. Every value must be an integer `>=1`;
an entry greater than one on `C` raises a `ValueError`. The implementation pads
spatial inputs for grid/U-Net divisibility and uses receptive-field overlap for
tile assembly. Too many small tiles increase border overhead and can worsen
seams/runtime. Escalate from `(2,2)` to larger spatial counts only after a
small untiled crop succeeds. `return_predict=True` forces dense mode and can
defeat the memory plan.

## Scaling

`scale` may be a positive scalar, or one positive value per input axis:

- `YX`: scalar or `(sY,sX)`;
- `YXC`: scalar or `(sY,sX,1)`.

The model uses `scipy.ndimage.zoom` with linear interpolation internally,
leaves non-spatial axes at one (warning/replacing any other value), and maps
polygon points/distances back to the original coordinates. Returned labels keep
the original spatial shape. Do not both resize the image externally and pass
`scale` unless double resampling is deliberate. A scale above one increases
memory; compare points, coordinates, probabilities, and a held-out result with
a separately resized reference before adopting it.

## `predict_instances_big` contract

```python
model.predict_instances_big(
    img, axes, block_size, min_overlap, context=None,
    labels_out=None, labels_out_dtype=np.int32,
    show_progress=True, **kwargs,
)
```

Example for RGB:

```python
labels, polys = model.predict_instances_big(
    img, axes="YXC", block_size=4096,
    min_overlap=128, context=128,
    normalizer=normalizer, n_tiles=(4,4,1),
)
```

The implementation reads overlapping blocks, calls `predict_instances`, crops
context, filters objects to the responsible block, relabels sequentially,
writes labels, and concatenates global polygon details. It is intended to
match direct prediction when its object-size assumptions hold.

### Block invariants

- Every predicted object must be smaller than `min_overlap` in the relevant
  spatial dimensions. A violation raises a `RuntimeError` naming the object
  shape and required overlap; increase `min_overlap` and often `block_size`.
- Every spatial axis must satisfy
  `0 <= min_overlap + 2*context < block_size`.
- `block_size`, `min_overlap`, and `context` can be scalars or tuples with one
  entry per input axis. Values are increased to grid-compatible multiples and
  effective values are printed. Choose compatible values in advance.
- For `YXC`, the C block is forced to the full channel size and its overlap and
  context are set to zero. Channel tiling cannot fix a channel mismatch.
- A block must fit within its corresponding input dimension and leave enough
  room for the receptive field, context, and expected object.
- `context=None` uses an automatic receptive-field estimate. For production,
  explicit context at least as large as the model overlap recommendation is
  easier to audit.

`predict_instances_big` forces inner `axes`, `overlap_label=None`,
`return_labels=True`, and `return_predict=False`; it also disables inner tile
progress when outer progress is enabled. Do not expect overlap-label or dense
raw-map output through this route.

## Output stores

The output label shape is the input shape with `C` removed. With
`labels_out=None`, a NumPy-like integer array of `labels_out_dtype` (default
`np.int32`) is allocated. A supplied writable NumPy-like/chunked store must
have exactly that spatial shape. `labels_out=False` suppresses label writing
and, in this revision, returns `None` in the label position while still
returning polygon details.

For 2D, `polys` contains global `prob`, `points`, and `coord` arrays; a
multiclass model may also supply `class_prob` and `class_id`. Polygon details
can remain large even when labels are streamed. If only labels are needed, do
not retain `polys` unnecessarily.

## Validation and recovery

1. Run direct prediction and block prediction on a small crop with objects
   comfortably below `min_overlap`.
2. Compare labels using high-IoU instance matching and compare sorted `points`,
   `coord`, and `prob` arrays, as the native 2D big-data test does.
3. Repeat for `YX` and `YXC` if both forms are supported; for YXC check
   `n_tiles=(ny,nx,1)` and output shape excluding C.
4. Test the selected label store/dtype and, if used, the `labels_out=False`
   polygon-only path. Record effective block values, context, peak RAM, and
   any object-size violation.
5. For a read-only or chunked input, use a normalizer whose `before(x,axes)`
   can handle each block. A Zarr-like store is optional and not part of the
   CPU StarDist baseline.

If a process is killed without a Python exception, treat it as memory pressure:
reduce concurrent jobs, increase spatial `n_tiles`, keep sparse mode, avoid
`return_predict`, and then move to block-wise inference. Do not change
thresholds to hide an OOM.
