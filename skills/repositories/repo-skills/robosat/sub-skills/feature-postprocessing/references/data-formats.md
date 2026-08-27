# Feature post-processing data formats

## Slippy Map directory layout

RoboSat post-processing commands read and write tiled directories with numeric `z/x/y` paths:

```text
<root>/
  18/
    69108/
      105091.png
      105092.png
```

Rules:

- `z`, `x`, and `y` path components must parse as integers.
- File extensions may vary for imagery inputs, but probability, label, mask, and compare outputs here are PNGs.
- Commands pair corresponding tiles by zoom/x/y. Keep probability, image, label, and mask trees synchronized before running multi-input commands.
- Tile sizes must match for `rs compare`; post-processing masks commonly follow the model prediction tile size.

## Quantized binary probability PNGs

`rs predict` writes one PNG per tile for binary segmentation output. The PNG stores the foreground class probability only.

Encoding assumptions:

- Image mode is palette-compatible single-channel PNG.
- Pixel value is an integer in `[0, 255]`.
- Values are quantized anchors for foreground probability in `[0.0, 1.0]`.
- Background probability is reconstructed as `1.0 - foreground`.
- The original model output had exactly two classes and probabilities summed to one.

Implications:

- This format is not a general multi-class probability tensor format.
- `rs masks` cannot recover more than background/foreground from these PNGs.
- Ensemble inputs to `rs masks` must represent the same binary class semantics and tile set.
- The probability PNG palette is only a visualization aid; the pixel values carry the numeric foreground probabilities.

## Palette mask PNGs

`rs masks` writes class-index PNGs in `P` mode.

Conventions:

- Class `0` is background.
- Class `1` is foreground for default binary parking workflows.
- The default mask palette uses a dark denim-like background color and an orange foreground color.
- `rs features` reads masks as palette images and compares class indices, not RGB colors.

Dataset config dependency:

```toml
[common]
classes = ["background", "parking"]
colors = ["denim", "orange"]
```

`rs features --type parking` finds the mask index by locating `parking` in `common.classes`. If the class order does not match the masks, features will be extracted from the wrong pixels.

## Parking GeoJSON FeatureCollections

`rs features` writes a GeoJSON FeatureCollection of WGS84 polygons:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [[lon, lat], [lon, lat], [lon, lat], [lon, lat]]
        ]
      },
      "properties": {}
    }
  ]
}
```

Expected geometry semantics:

- Coordinates are WGS84 longitude/latitude pairs.
- Rings are closed: first and last coordinate match.
- `Polygon` is the normal output from feature extraction; later merge can produce `MultiPolygon`.
- Invalid polygons are skipped during feature extraction.
- Feature extraction may produce no features when masks are empty or morphology removes all foreground.

Validate with:

```bash
python sub-skills/feature-postprocessing/scripts/validate_feature_collection.py out/features.geojson
```

## Merge output

`rs merge` reads a predicted FeatureCollection and writes another FeatureCollection.

Changes to expect:

- Adjacent shapes whose meter-buffered geometries intersect can become one component.
- Geometry may be `Polygon` or `MultiPolygon`.
- A property named `area` is added when a merged shape is accepted. It is an integer square-meter area computed in an equal-area projection and rounded to whole square meters.
- Shapes that become invalid, or that merge into unsupported geometry types, are skipped with warnings.

Threshold semantics:

- `--threshold` is a distance in meters.
- The code buffers by the threshold, unions connected components, then buffers back by the negative threshold.
- At z18, small thresholds are usually appropriate for seam/crack cleanup; large thresholds can over-merge distinct features.

## Dedupe output

`rs dedupe` compares predicted features against existing OSM-derived features.

Input assumptions:

- Both inputs are GeoJSON FeatureCollections.
- Both use WGS84 polygonal coordinates.
- The OSM input should represent features that are already known and should not be proposed again.

Output behavior:

- Predictions with no nearby/intersecting OSM geometry are kept.
- Predictions with intersecting OSM geometry are kept only when IoU is below `--threshold`.
- Output features are geometry-only GeoJSON features; properties from the predicted input are not preserved by the CLI.

Threshold semantics:

- `--threshold` is maximum allowed IoU for keeping a prediction.
- Lower values drop more overlapping predictions.
- Higher values keep predictions unless they almost duplicate existing OSM features.

## Compare mosaic output

`rs compare` writes Slippy Map RGB PNGs for visual QA.

Columns:

1. Source image tile.
2. Label tile.
3. First mask directory.
4. Additional mask directories, one column each.

Filtering:

- `--minimum` and `--maximum` filter on the fraction of non-background pixels in each mask.
- A tile is kept if at least one provided mask satisfies the percentage interval.
- The implementation treats every pixel value other than `0` as foreground, so the filter is binary-oriented.

Validation:

- Every input tree must contain the same tile names.
- The image, label, and mask sizes for a tile must match exactly.
- The output image width equals `(2 + number_of_mask_dirs) * tile_width`; height equals `tile_height`.
