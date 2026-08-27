# Feature post-processing workflows

These recipes assume RoboSat is installed and exposes the `rs` console command. If `rs` is not on `PATH`, use the module form instead: `python -m robosat.tools <subcommand> ...`.

The bundled script examples below are written relative to the generated RoboSat skill root. If you are running from the `feature-postprocessing` sub-skill directory itself, drop the leading `sub-skills/feature-postprocessing/` prefix.

## Inputs and outputs at a glance

| Stage | Command | Required input | Output | Notes |
| --- | --- | --- | --- | --- |
| Probability to class mask | `rs masks` | One or more Slippy Map probability PNG directories | Slippy Map `P`-mode mask PNGs | Binary foreground probabilities only. |
| Mask to parking vectors | `rs features` | Mask Slippy Map directory and dataset TOML | GeoJSON FeatureCollection | Default CLI registers only `parking`. |
| Merge adjacent vectors | `rs merge` | Predicted GeoJSON FeatureCollection | GeoJSON FeatureCollection | Threshold is distance in meters. |
| Drop existing OSM overlaps | `rs dedupe` | OSM GeoJSON and predicted GeoJSON | GeoJSON FeatureCollection | Threshold is maximum IoU allowed to keep a prediction. |
| Visual QA mosaic | `rs compare` | Image, label, and one or more mask Slippy Map directories | Slippy Map RGB mosaic PNGs | Filters by non-background percentage. |

## 1. Convert probability PNGs to masks

Single prediction run:

```bash
rs masks out/masks probs/run-a
```

Soft-vote two prediction runs:

```bash
rs masks out/masks probs/run-a probs/run-b --weights 0.6 0.4
```

Validation checklist:

- Every probability input is a Slippy Map tree with matching zoom/x/y tile names.
- Probability PNGs are single-channel, 8-bit, palette-compatible images where pixel value `0` means foreground probability near `0.0` and `255` means foreground probability near `1.0`.
- The model was binary. RoboSat reconstructs the background channel as `1 - foreground`; multi-class probability tensors are not represented by this PNG format.
- If you use `--weights`, provide exactly one weight per probability directory.

Useful smoke check:

```bash
python sub-skills/feature-postprocessing/scripts/softvote_smoke.py
```

Expected output: `softvote smoke passed` plus a tiny deterministic mask.

## 2. Extract parking GeoJSON from masks

A minimal dataset TOML must include the class order used by the masks. For default parking runs, `parking` is commonly class index `1`:

```toml
[common]
classes = ["background", "parking"]
colors = ["denim", "orange"]
```

Run feature extraction:

```bash
rs features out/masks --type parking --dataset dataset.toml out/features.geojson
```

Validation checklist:

- The mask directory uses zoom 18 tiles. The default parking handler raises an error for other zoom levels because its morphology thresholds are tuned for z18.
- The dataset config contains `parking`; RoboSat finds the mask class index from `common.classes`.
- Mask PNG values use class indices, not RGB colors. Palette colors are only for visualization.
- Empty output can be valid when masks contain no foreground pixels after denoise/grow morphology.

Validate the GeoJSON artifact:

```bash
python sub-skills/feature-postprocessing/scripts/validate_feature_collection.py out/features.geojson --expect-nonempty
```

Drop `--expect-nonempty` when an empty tile set or high-confidence filtering is expected.

## 3. Merge adjacent predicted polygons

Merge close polygons into connected components before dedupe or manual review:

```bash
rs merge out/features.geojson --threshold 3 out/features-merged.geojson
```

How to choose the threshold:

- The threshold is meters, not pixels or degrees.
- Start small, such as `1` to `5`, for parking-lot cleanup at z18.
- A larger value can bridge tile-edge cracks but may also merge distinct nearby lots.

Validation checklist:

- Inputs should be WGS84 Polygon or MultiPolygon features.
- Invalid intermediate geometries are skipped with warnings.
- Merged features get an `area` property computed after equal-area projection and rounded to square meters.

Validate merged output:

```bash
python sub-skills/feature-postprocessing/scripts/validate_feature_collection.py out/features-merged.geojson --expect-nonempty
```

## 4. Dedupe predictions against known OSM features

Dedupe removes predictions that sufficiently overlap existing OSM-derived features:

```bash
rs dedupe osm-existing.geojson out/features-merged.geojson --threshold 0.5 out/features-new.geojson
```

Interpretation of `--threshold`:

- For each prediction, RoboSat unions intersecting OSM shapes and computes IoU against the prediction.
- The prediction is kept only when IoU is less than the threshold.
- Lower thresholds are stricter and drop more predictions; higher thresholds keep predictions unless overlap is very high.
- This is not a model probability threshold.

Validation checklist:

- Both input files are GeoJSON FeatureCollections.
- Coordinates are WGS84 lon/lat polygons, not projected meters.
- Dedupe output may omit properties from the prediction input because the CLI writes geometry-only features.

## 5. Produce visual compare mosaics

Compare imagery, ground-truth labels, and one or more predicted mask runs:

```bash
rs compare out/compare images labels out/masks
```

With two mask runs and foreground-percentage filtering:

```bash
rs compare out/compare images labels out/masks baseline/masks --minimum 0.01 --maximum 0.95
```

Output format:

- The output is a Slippy Map tree of RGB PNG mosaics.
- Columns are: image, label, then each predicted mask directory in the order provided.
- `--minimum` and `--maximum` filter by the percentage of pixels whose mask value is not `0`.

Validation checklist:

- Image, label, and all mask directories contain the same zoom/x/y tile names.
- Corresponding image, label, and mask sizes match exactly.
- Filtering logic is binary-oriented; multi-class masks are treated as "non-background" when value is not `0`.

## 6. Recommended end-to-end post-processing sequence

```bash
# 1. Binary probabilities to visualization masks.
rs masks work/masks work/probs

# 2. Parking masks to WGS84 GeoJSON polygons.
rs features work/masks --type parking --dataset dataset.toml work/features.geojson

# 3. Merge close polygons across cracks and tile seams.
rs merge work/features.geojson --threshold 3 work/features-merged.geojson

# 4. Remove predictions already represented in OSM-derived features.
rs dedupe osm-existing.geojson work/features-merged.geojson --threshold 0.5 work/features-new.geojson

# 5. Inspect image/label/mask agreement.
rs compare work/compare images labels work/masks --minimum 0.01 --maximum 0.95

# 6. Validate vector artifact structure and geometry.
python sub-skills/feature-postprocessing/scripts/validate_feature_collection.py work/features-new.geojson
```

Stop and route back to `model-lifecycle` if the probability tiles do not exist yet. Stop and route to `data-preparation` if the OSM-existing GeoJSON or training labels still need to be created.
