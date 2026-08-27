# Feature post-processing troubleshooting

## `rs masks` fails because weights do not match probability inputs

Symptom:

```text
Error: number of slippy map directories and weights must be the same
```

Fix:

- Provide exactly one `--weights` value per probability directory.
- Or omit `--weights` to use an unweighted average.

Example:

```bash
rs masks out/masks probs/a probs/b --weights 0.5 0.5
```

## Probability PNGs do not match RoboSat's binary assumptions

Symptoms:

- Masks look inverted or all foreground/background.
- Ensemble outputs disagree unexpectedly.
- A non-RoboSat probability export cannot be converted with `rs masks`.

Causes:

- RoboSat stores only the foreground channel as an 8-bit PNG and reconstructs background as `1 - foreground`.
- The post-processing code assumes the original model had exactly two classes.
- Multi-class logits/probabilities need a different storage and argmax path.

Fix:

- Confirm that probability PNG pixel values encode foreground probability on a `0..255` scale.
- Confirm that every probability directory uses the same class semantics.
- If the model is multi-class, route back to model/prediction handling and produce an explicit multi-class mask format instead of using `rs masks` unchanged.

## Probability directories are not tile-synchronized

Symptoms:

- Missing output masks.
- Wrong masks for a tile.
- Assertions or file-not-found errors in downstream `features` or `compare`.

Causes:

- Input Slippy Map trees do not contain identical zoom/x/y tiles.
- Filesystem iteration order is not a reliable semantic match across different directories.

Fix:

- Compare tile lists before ensembling.
- Ensure each probability directory has the same `z/x/y.png` names.
- Remove nonnumeric directories or files that should not be parsed as tiles.

## `rs features` says parking thresholds are tuned for z18

Symptom:

```text
NotImplementedError: Parking lot post-processing thresholds are tuned for z18
```

Cause: the default parking handler checks `tile.z == 18` before applying denoise/grow/simplify thresholds.

Fix options:

- Run parking post-processing on z18 masks.
- If a different zoom is required, implement and verify a custom handler with retuned morphology thresholds before using it for production output.

## `rs features --type` rejects a feature type

Symptoms:

- CLI argument error for `--type building`, `--type road`, or another class.
- Dataset contains a class, but the CLI does not accept it.

Cause: the default installed post-processing CLI registers only the parking handler.

Fix:

- Use `--type parking` for default RoboSat post-processing.
- For new feature classes, implement a handler with `apply(tile, mask)` and `save(path)`, then register it in the installed package before relying on the CLI.
- Creating training labels for other OSM features is a data-preparation task, not this post-processing step.

## Dataset class order does not match mask values

Symptoms:

- `rs features` emits empty output although masks visibly contain foreground.
- Features are extracted from the wrong class.

Cause: `rs features` locates the mask index by finding the requested type, such as `parking`, in `common.classes`.

Fix:

- Ensure the dataset TOML uses the same class order as the model and masks.
- For default binary parking masks, use `classes = ["background", "parking"]` so parking is index `1`.

## Empty feature output

Possible causes:

- Masks are all background.
- Class index mismatch between masks and dataset config.
- Denoise/grow/simplify thresholds removed small components.
- Tile zoom is not z18 and processing stopped.
- Probability thresholding or prediction quality produced weak foreground signal before `rs masks`.

Checks:

```bash
python sub-skills/feature-postprocessing/scripts/softvote_smoke.py
python sub-skills/feature-postprocessing/scripts/validate_feature_collection.py out/features.geojson
```

Then inspect a few mask PNGs directly and confirm that foreground pixels have value `1`, not only an RGB palette color.

## Invalid polygons or skipped rings

Symptoms:

- Warnings about invalid extracted or merged features.
- Fewer features than expected.
- Validator reports self-intersections or non-polygon geometries.

Causes:

- Noisy masks create self-intersecting contours.
- Simplification turns small contours into fewer than three points.
- The parking handler only handles one level of holes and skips deeper nesting.
- Merge buffering/unbuffering can create invalid geometry for complex shapes.

Fix:

- Validate the output GeoJSON with `validate_feature_collection.py`.
- Review masks visually with `rs compare`.
- Try a smaller merge threshold if invalid geometry appears after merge.
- For custom handlers, tune denoise/grow/simplify thresholds and validate on representative tiles.

## `rtree` or `libspatialindex` import failure

Symptoms:

```text
ImportError: libspatialindex_c.so: cannot open shared object file
```

or other `rtree` load errors during `rs merge`, `rs dedupe`, or module import.

Cause: Python package `rtree` requires the native `libspatialindex` library.

Fix examples:

- Conda-style environment: install `libspatialindex` from a compatible channel.
- Debian/Ubuntu-style system: install the OS package that provides spatialindex before installing or importing `rtree`.
- Re-run `rs merge --help` or `rs dedupe --help` after the native library is available.

## `pyproj` cannot resolve `ESRI:54009`

Symptoms:

- CLI import fails before running a command.
- Error mentions `ESRI:54009`, missing projection data, or invalid CRS.

Cause: spatial helpers construct an equal-area transformer for `ESRI:54009`; older or incomplete projection databases may not know that CRS.

Fix options:

- Use a `pyproj` version and projection database that can resolve `ESRI:54009` while staying compatible with RoboSat's Python-era dependency range.
- Ensure projection data files are installed and discoverable by `pyproj`.
- After changing projection packages, run `rs --help`, `rs merge --help`, and a small GeoJSON validator run before processing large outputs.

## Merge threshold over-merges or under-merges

Symptoms:

- Separate parking lots become one feature.
- Tile-edge cracks remain unmerged.

Cause: `rs merge` buffers WGS84 shapes in a meter-based projection by `--threshold`, builds connected components, then unbuffers.

Fix:

- Use a smaller threshold to avoid bridging distinct objects.
- Use a slightly larger threshold to close small seams.
- Validate area and geometry after each trial threshold.

## Dedupe drops too many or too few predictions

Symptoms:

- Almost all predictions disappear.
- Existing OSM features are still duplicated.

Cause: `rs dedupe --threshold` is IoU, not meters or confidence.

Fix:

- Lower threshold: stricter duplicate removal, more predictions dropped.
- Higher threshold: only high-overlap predictions are dropped.
- Ensure OSM and prediction GeoJSON use the same WGS84 coordinate space and comparable polygon extents.

## `rs compare` misses tiles or raises size assertions

Symptoms:

- Missing mosaics.
- Assertion failure that image and label/mask sizes differ.
- File-not-found for a label or mask path.

Fix:

- Synchronize image, label, and all mask Slippy Map trees by zoom/x/y.
- Ensure tile sizes match exactly.
- Remember that compare output is filtered: if all masks fall outside `--minimum`/`--maximum`, no mosaic is written for that tile.
