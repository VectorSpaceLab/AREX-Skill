# Classical image-operations troubleshooting

Use the smallest safe reproduction first. The validator is read-only and can
separate file/array failures from failures at the legacy GIMP boundary.

## Validation and shape failures

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `unsupported rank` or empty shape | Input is scalar, 1-D, 4-D, or has a zero-sized axis. | Supply an image-like `(H,W)` or `(H,W,C)` array with positive dimensions. Do not flatten a batch or silently squeeze a semantic axis. |
| `unsupported channel count` | Final channel dimension is not 1, 3, or 4, or a grayscale file was interpreted unexpectedly. | Inspect the reported shape. For grayscale use `(H,W)` or `(H,W,1)`; for K-means use RGB/RGBA only. Do not drop arbitrary channels without recording it. |
| expected size mismatch | A cropped, offset, or resized layer does not equal the image container. | In a compatible GIMP session, use **Layer -> Layer to Image Size** for the source layer. For a file, correct the expected dimensions or resize intentionally in a separate, documented step. |
| dtype rejected or values out of range | Object/string/complex data, NaN/Inf, negative values, or values above the selected maximum. | Export numeric image data and validate again. For normalized floats, pass an explicit range such as `--max-value 1`; do not cast because `uint8` casting can wrap or truncate. |
| input cannot be read | Missing path, unsupported image format, corrupt file, or a pickled/object `.npy`. | Check the explicit path and format. The helper intentionally uses safe NumPy loading without pickle and does not search or download alternatives. |
| validator reports a memory/size guard failure | `H*W*C` is too large for a safe check or an explicit `--max-elements` limit was exceeded. | Use a smaller fixture, raise the limit only with a memory budget, or validate metadata separately. Do not make a full copy just to reshape. |

## K-means failures

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| Message asking for Layer to Image Size | Layer height or width differs from the image height or width. | Apply the layer-to-image-size prerequisite, revalidate, and retry. The source path does not automatically resample or pad. |
| reshape/feature error for grayscale or two-channel input | The implementation expects three color columns after optional RGBA reduction. | Convert to an intentional RGB representation before K-means or choose another operation. Do not claim grayscale support based only on the registration wildcard. |
| invalid or failing cluster count | `K <= 0`, `K > H*W`, non-integer input, or too few useful observations. | Choose an integer in `1..H*W`; begin with `K=2` or `K=3` on a small image. Degenerate colors can still produce empty-cluster warnings. |
| output differs between runs | SciPy `kmeans2` is called without a seed or fixed centers. | Treat the result as stochastic. For reproducible research, wrap the numerical step with controlled initialization and record the library/version; do not edit a live image until the policy is clear. |
| position-enabled output looks spatially segmented | Raw `x,y` coordinates were appended to RGB features and were not normalized. | Disable position for color-only quantization, or compare dimensions and coordinate scaling deliberately. Record the boolean because it changes the algorithm's feature space. |
| result layer write fails or is corrupted | Result shape, byte count, channel count, or destination layer type is incompatible. | Stop before writing; verify `(H,W,C)`, image dimensions, and `uint8` byte length. Do not rely on implicit conversion or stale layer metadata. |
| no new layer after a run | Size preflight short-circuited, numerical code raised an error, or the live PDB/plugin runtime is incompatible. | Check the GIMP message/progress output and source/destination dimensions. A successful pure-NumPy test does not prove that `gimpfu` and pixel-region writes work. |

## Inversion and palette boundaries

- Inversion is the source's in-place PDB operation inside an undo group. If a
  user expects a new layer, use a separately implemented array adapter and
  clearly label it as non-destructive adapter behavior; do not promise that the
  legacy `Invert` menu entry creates one.
- The palette entry does not consume the current drawable or calculate dominant
  colors. It depends on a packaged palette image and opens a separate `palette`
  image. If it fails, check packaging and OpenCV image decoding in a compatible
  runtime; do not diagnose it as a K-means channel issue.
- GIMP/Python 2 absence is an explicit verification limit. Do not attempt to
  install, mutate, or emulate GIMP through this helper, and do not substitute a
  service or model call.

## Memory and safe recovery

K-means first flattens all pixels and may append two more columns for position.
The approximate feature storage is proportional to `H*W*3` float32 values
without position and `H*W*5` with position, plus SciPy work arrays and the
cluster centers. Reduce spatial dimensions before increasing K. Prefer a
read-only small fixture to a repeated full-size retry. A `MemoryError`, process
kill, or incomplete output is not evidence of a successful result; discard the
partial in-memory result and start again with a bounded input.

Never solve a failure by enabling network access, adding credentials, loading
weights, invoking a model service, or writing over the source image. Those are
outside this sub-skill.
