# Classical image-operation workflows

These workflows separate deterministic array checks from the legacy GIMP
boundary. They describe behavior distilled from the repository manual and
classical plug-in implementations; they do not require access to the source
checkout.

## Array preflight

Use this route before adapting a file-based array or before trying to diagnose a
pixel-region failure.

1. Choose one explicit `.npy` or image file. Do not let a script discover files,
   download input, or overwrite an image.
2. Run the bundled helper from this sub-skill directory, for example:

   ```text
   python scripts/validate_image_array.py input.npy --channels 3 --expected-size 64 96
   ```

   For a grayscale array, a two-dimensional `(H, W)` shape is interpreted as
   one channel. A three-dimensional `(H, W, 1)` shape is also valid when
   `--channels 1` is requested.
3. Read the reported shape, channel count, dtype, and observed range. The
   default range is inclusive `0..255`, matching the byte-oriented GIMP pixel
   region convention. Use an explicit `--max-value` only when the source array
   intentionally uses another numeric scale.
4. Stop on any nonzero exit. Fix the file, shape, or expectation rather than
   casting or reshaping blindly. The helper never writes a converted file.
5. For K-means, continue only with RGB `(H,W,3)` or RGBA `(H,W,4)` input. Remove
   alpha deliberately, if desired, and record that choice; the source operation
   drops alpha before clustering.

## GIMP drawable to array

This is a static contract for a compatible GIMP/Python 2 runtime, not a verified
command to execute in the current environment.

1. Select the target image and its intended drawable/layer.
2. Read the whole pixel region starting at `(0, 0)` using the drawable width and
   height. Interpret the returned bytes as unsigned 8-bit values and reshape to
   `(layer_height, layer_width, bytes_per_pixel)`.
3. Compare layer dimensions with the containing image dimensions. If they differ,
   use **Layer -> Layer to Image Size** in GIMP before K-means. Do not silently
   pad, crop, or resize in an adapter unless that behavior is explicitly part of
   the task.
4. Confirm channels. RGB is three bytes per pixel; RGBA is four. Alpha is kept by
   the generic conversion and removed only by operations that say so.
5. Keep a reference to the source layer and image separately. The image owns
   newly inserted layers; the drawable owns the input pixels.

## Inversion route

The registered inversion procedure accepts an image and a drawable. It starts an
undo group, calls the PDB invert operation on that drawable, and ends the undo
group. It reports progress using the layer name. This is an in-place operation
in the evidence, not a new result-layer operation.

For a pure-array analogue, use `255 - array` only after validating an unsigned
byte or explicitly bounded numeric array. Preserve the original array if a
non-destructive result is required. If integrating the analogue into a GIMP
adapter, create a destination layer using the result-layer contract below and
label that as adapter behavior—not as behavior verified from the inversion
plug-in.

## K-means route

The registered procedure receives the image, a current drawable, an original
image layer, an integer cluster count, and a boolean position flag. The practical
sequence is:

1. Read `drawinglayer` with the channel-data contract.
2. If the layer is not image-sized, report the Layer-to-Image-Size prerequisite
   and do not continue.
3. If the array has four channels, retain only RGB. Reshape RGB pixels to
   `(H*W, 3)` and convert features to `float32`.
4. If `position` is true, append flattened `x` and `y` pixel coordinates, giving
   each row five features `(R,G,B,x,y)`. Otherwise use only `(R,G,B)`.
5. Run SciPy `kmeans2` with the requested number of clusters. The source does
   not set a random seed or provide initial centers, so this step is not
   guaranteed reproducible.
6. Convert cluster centers to `uint8`, map each pixel's assignment to its color,
   reshape to `(H,W,3)`, and pass it to the result-layer helper.

Before step 5, enforce a positive integer cluster count no larger than `H*W`.
For a deterministic experiment, an external adapter must control initialization
or record the seed/centers and library version; do not silently advertise the
legacy default as deterministic.

## Position-feature decision

Use `position=False` when spatially distant pixels with the same color should be
eligible for the same cluster and the task is primarily color quantization. Use
`position=True` when spatial locality should influence assignments. Coordinates
are appended at their raw pixel scale; they are not normalized in the source.
Therefore the image dimensions and coordinate scale affect the balance between
color and location. Compare both settings on a tiny fixture before using a large
image, and record the choice in the result notes.

## Result-layer route

For array-producing operations that follow the shared helper pattern:

1. Ensure the result is a non-empty `H x W x C` byte-compatible array.
2. Ensure `H` and `W` match the destination image. Ensure the number of bytes per
   pixel matches the layer type selected by the adapter.
3. Cast or clip intentionally to `uint8`; do not rely on an implicit narrowing
   conversion for out-of-range values.
4. Create the layer with the image dimensions and full opacity, write the whole
   pixel region, add it at stack position zero, and flush displays.
5. Verify that a new layer exists and inspect its dimensions. `new_output` is a
   common source label, not a durable API identifier.

The palette plug-in is an exception: it reads a bundled palette image, converts
OpenCV's BGR read to RGB, creates a separate image called `palette`, and does
not consume the active drawable. Treat it as a static palette display. A true
current-layer palette extraction workflow is not evidenced by this sub-skill.
