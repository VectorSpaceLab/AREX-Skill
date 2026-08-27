# Data formats

## Slippy Map layout

A Slippy Map tree stores tile files as:

```text
<root>/<z>/<x>/<y>.<ext>
```

- `z`, `x`, and `y` are decimal integers.
- The extension can vary by source format.
- Tile identity is the `z/x/y` coordinate triple, not the filename extension.
- Keep imagery, masks, and any derived subsets aligned on the same tile ids.

## Tile CSV

Tile CSV files are line-delimited, one tile per row.

```text
x,y,z
```

- No header is required or assumed.
- Values must be integers.
- The CSV format is used by `rs cover`, `rs download`, `rs rasterize`, and `rs subset`.
- If you need deterministic order, sort the CSV yourself after generation.

## GeoJSON

- `rs extract` emits GeoJSON `FeatureCollection` data.
- `rs cover` reads the `features` array from a GeoJSON `FeatureCollection`.
- `rs rasterize` expects Polygon or MultiPolygon features in WGS84 lon/lat coordinates.
- Invalid or unsupported features may be skipped by the OSM handlers or warned about during rasterization.
- If `rs extract` emits multiple chunks, combine them before a single downstream `cover` run or keep `--batch` above the expected feature count.

## Dataset TOML

Dataset configs use TOML with at least these tables:

```toml
[common]
dataset = "<dataset-root>"
classes = ["background", "parking"]
colors = ["denim", "orange"]

[weights]
values = [1.6248, 5.762827]
```

- `[common].dataset` points to the dataset root.
- `[common].classes` names the label indices starting at zero.
- `[common].colors` defines the palette names for those labels.
- `[weights].values` stores the output of `rs weights`.
- `classes` and `colors` must have the same length.
- `rs rasterize` in this release expects exactly two classes and two colors.

## Dataset root layout

```text
<dataset-root>/
  training/
    images/
    labels/
  validation/
    images/
    labels/
```

- `training/labels` is the source for class-weight computation.
- Each image split and label split should cover the same tile ids.
- Use `rs subset` to copy a matching tile list across image and label trees.

## Mask encoding

- Masks are single-channel PNGs with a palette attached for quick inspection.
- Class indices start at zero.
- The palette is for visualization only; downstream consumers should read the indexed values.
- Existing mask tiles are merged with pixel-wise maximum when rasterization runs again.

## Color names

The built-in palette names include:

- `dark`
- `gray`
- `light`
- `white`
- `cyan`
- `blue`
- `bluedark`
- `denim`
- `navy`
- `navydark`
- `purple`
- `teal`
- `green`
- `yellow`
- `mustard`
- `orange`
- `red`
- `pink`

Use the names exactly as spelled in the config and palette helpers.
