# Classical image-operations API reference

This is a distilled reference for the legacy Python/GIMP-Fu registrations and
the shared helper patterns. It is documentation, not a promise that the current
host can import `gimpfu`: GIMP and Python 2 were unavailable during inspection.

## Registered procedures

| Procedure | Inputs exposed by registration | Evidence-backed behavior |
| --- | --- | --- |
| `Invert` | `image: PF_IMAGE`, `drawable: PF_DRAWABLE` | Starts an undo group, calls the PDB invert operation on the drawable, then ends the group. Mutates the selected drawable; no result-layer helper is called. |
| `kmeans` | `image: PF_IMAGE`, `drawable: PF_DRAWABLE`, `drawinglayer: PF_LAYER`, `depth: PF_INT` default `3`, `position: PF_BOOL` default `False` | Reads `drawinglayer`, checks it against image dimensions, clusters RGB pixels, and creates a `new_output` layer when successful. |
| `colorpalette` | no image, drawable, or user arguments | Reads the bundled palette image, changes OpenCV BGR ordering to RGB, and opens a separate image named `palette`. It is not current-layer palette extraction. |

The registration wildcard `*` on the first two procedures denotes broad image
compatibility at registration time; it does not make every channel layout safe
for K-means. Validate actual bytes and dimensions first.

## `channelData(layer)` contract

The shared implementation performs the following operations:

| Stage | Contract |
| --- | --- |
| Region | Request the entire pixel region from `(0, 0)` through `layer.width` and `layer.height`. |
| Bytes | Read the region as a byte buffer and interpret it as `np.uint8`. |
| Channels | Use `region.bpp` as the final dimension. |
| Shape | Reshape to `(layer.height, layer.width, region.bpp)`. |
| Side effects | None intended; it is a read of the drawable's pixels. |

This helper does not account for a layer offset, crop, mask semantics, or image
mode conversion. A two-dimensional grayscale representation in a file helper
is a one-channel convenience; a live GIMP region normally still has an explicit
bytes-per-pixel dimension.

## K-means feature contract

Let `image` be the array returned by `channelData`.

1. If `image.shape[0] != imggimp.height` or `image.shape[1] != imggimp.width`,
   the procedure emits a user message asking for **Layer -> Layer to Image Size**
   and skips clustering.
2. If `image.shape[2] == 4`, it replaces the array with its first three channels.
3. It sets `h, w, d = image.shape`, reshapes pixels to `(-1, 3)`, and casts to
   `float32`.
4. When `locflag`/`position` is true, it appends flattened mesh-grid `x` and `y`
   coordinates. The feature row is then `(R,G,B,x,y)`.
5. It calls SciPy `kmeans2(pixel_values, n_clusters)` without a seed or explicit
   initialization.
6. With position enabled, it keeps only the first three center columns before
   converting centers to `uint8`. Otherwise all center columns are RGB.
7. It indexes centers by the flattened assignments, reshapes to `(h,w,d)`, and
   calls `createResultLayer(imggimp, 'new_output', segmented_image)`.

The source does not validate `n_clusters`, reject non-finite values, normalize
coordinates, or guarantee stable cluster IDs. An adapter should validate
`n_clusters >= 1` and `n_clusters <= h*w` before invoking the numerical routine.
A cluster ID permutation is not necessarily a visual difference.

## `createResultLayer(image, name, result)` contract

The classical helper:

1. Converts `result` to `np.uint8` and obtains its raw bytes.
2. Creates a layer using `image.width` and `image.height`, with full opacity and
   normal blend mode.
3. Writes the bytes to the complete destination pixel region.
4. Adds the layer at stack position zero and flushes displays.

The exact layer type argument differs among repository plug-ins, so an adapter
must select a type compatible with its channel count and GIMP version. The
helper itself does not verify result shape, byte length, range, or alpha
semantics. Validate these before the write. A safer pure-array contract is:

```text
result: uint8 array with shape (image.height, image.width, C)
C: compatible with the chosen destination layer type
side effect: one new top layer, or a clear error before any write
```

## Inversion contract

The inversion registration has the conceptual signature:

```text
invert(image, drawable) -> None
```

It initializes progress text using the drawable name, opens a PDB undo group,
invokes `gimp_invert(drawable)`, and closes the group. It does not return an
array or add a result layer. An array-level non-destructive analogue is
`inverted = 255 - array` for validated byte data, but that is an adapter-level
operation and must not be attributed to the live plug-in.

## Palette contract

The palette procedure has no user parameters and no current-drawable input. It
reads its packaged palette asset through OpenCV, uses `cvtColor(...,
COLOR_BGR2RGB)`, and builds a new RGB image and layer named `palette`. Missing or
unreadable assets are a packaging/runtime problem, not an image-array channel
problem. No evidenced algorithm extracts the dominant colors of the selected
layer; do not fill that gap with an undocumented OpenCV or SciPy implementation.

## Bundled validator interface

`../scripts/validate_image_array.py` is a bundled adapted helper, not an
original repository script. Its safe interface is:

| Option | Meaning |
| --- | --- |
| `input` | Required explicit `.npy` or image path. |
| `--channels {1,3,4}` | Require an exact supported channel count; default accepts only 1, 3, or 4. |
| `--expected-size HEIGHT WIDTH` | Require exact spatial dimensions. |
| `--require-dtype NAME` | Require a NumPy dtype name when supplied. |
| `--min-value VALUE`, `--max-value VALUE` | Inclusive numeric range; defaults are `0` and `255`. |
| `--max-elements N` | Optional early size guard before range scanning. |

It returns zero only when the input is readable, non-empty, rank 2/3, has a
supported channel count, meets requested dimensions/dtype, and has finite values
within the selected range. Failures are printed to stderr and return a
nonzero status. It never writes output, downloads data, invokes GIMP, or loads
model weights.
