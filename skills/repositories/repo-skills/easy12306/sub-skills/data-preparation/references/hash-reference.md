# Hash Reference

All supported hashes produce a packed 64-bit vector: 8 bytes from an `8x8` boolean matrix. The bundled script prints those bytes as 16-character hex strings.

Use [../scripts/hash_image_tiles.py](../scripts/hash_image_tiles.py) to compute whole-image or eight-tile hashes.

## `avhash`

1. Resize image to `8x8` with cubic interpolation.
2. Compute the average pixel value.
3. Compare each pixel with the average: `pixel > average`.
4. Pack the resulting 64 booleans with `numpy.packbits`.

## `phash`

This is the hash used by the legacy tile preprocessing workflow.

1. Resize image to `32x32` with cubic interpolation.
2. Apply a DCT over rows and columns: `dct(dct(image, axis=0), axis=1)`.
3. Keep the top-left `8x8` block.
4. Compute the median of that block.
5. Compare coefficients with the median: `coefficient > median`.
6. Pack with `numpy.packbits`.

## `phash_simple`

1. Resize image to `32x32` with cubic interpolation.
2. Apply SciPy DCT with default axis behavior.
3. Keep rows `0:8` and columns `1:9`.
4. Compare with the mean of that block.
5. Pack with `numpy.packbits`.

The command-line method name is `phash-simple`.

## `dhash`

1. Resize image to `9x8` with cubic interpolation.
2. Compare adjacent horizontal pixels: `image[:, 1:] > image[:, :-1]`.
3. Pack with `numpy.packbits`.

## `dhash_vertical`

1. Resize image to `8x9` with cubic interpolation.
2. Compare adjacent vertical pixels: `image[1:, :] > image[:-1, :]`.
3. Pack with `numpy.packbits`.

The command-line method name is `dhash-vertical`.

## Excluded `whash`

The source hash comparison file contains a wavelet-hash function that calls `pywt.wavedec2` and `pywt.waverec2`, but `pywt` is not imported there. The bundled script intentionally excludes `whash`; do not add it unless `PyWavelets` is installed, imported explicitly, and separately tested.

## Verification concept

The legacy hash verification concept loads a `captcha.npz` with `images` and `labels`, hashes each image, and reports collisions where the same hash maps to different labels. That native check requires external data and should not be used as the default validation gate. Use synthetic self-tests for script integrity and user-provided datasets for real collision analysis.
