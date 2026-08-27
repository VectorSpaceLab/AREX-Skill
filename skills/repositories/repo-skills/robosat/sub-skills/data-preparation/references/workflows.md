# Workflows

## Build a dataset from OSM and imagery

Use this when you need a fresh training set made from OpenStreetMap features and a Slippy Map imagery source.

```bash
rs extract --type parking <map.pbf> <features.geojson>
rs cover --zoom 18 <features.geojson> <tiles.csv>
rs download "tile-server.example/{z}/{x}/{y}.webp" \
  --ext webp \
  --rate 8 \
  <tiles.csv> \
  <images-root>
rs rasterize <features.geojson> <tiles.csv> <labels-root> \
  --dataset <dataset.toml> \
  --zoom 18 \
  --size 512
rs weights --dataset <dataset.toml>
python3 scripts/validate_slippy_map.py <images-root> --tiles-csv <tiles.csv>
python3 scripts/validate_slippy_map.py <labels-root> --tiles-csv <tiles.csv>
```

Notes:

- `rs extract` supports the built-in `parking`, `building`, and `road` handlers.
- The extractor can batch GeoJSON output; keep `--batch` high enough for one file if you want a simple downstream `cover` step.
- `rs cover` deduplicates tile ids across features, so the output CSV order is not stable.
- `rs download` skips files that already exist and preserves the extension from `--ext`.
- `rs rasterize` writes paletted PNG masks and merges with existing tiles via pixel-wise maximum.
- `rs weights` reads `training/labels` from the dataset root and prints a Python list suitable for `[weights].values`.

If the endpoint needs a token, inject it outside the skill tree and keep the command template generic.

## Refresh an existing dataset

Use this when imagery or labels already exist and you only need to realign or carve out a subset.

```bash
python3 scripts/validate_slippy_map.py <images-root> --tiles-csv <tiles.csv>
python3 scripts/validate_slippy_map.py <labels-root> --tiles-csv <tiles.csv>
rs subset <images-root> <tiles.csv> <subset-images-root>
rs subset <labels-root> <tiles.csv> <subset-labels-root>
rs weights --dataset <dataset.toml>
```

Notes:

- Keep the image and label tile sets identical before recomputing weights.
- `rs subset` preserves the source file extension when it copies tiles.
- Recompute weights whenever the training masks change in a way that affects class balance.

## Validate before rasterization

Use the validator before a rasterize or weights job when you suspect tile-list drift.

```bash
python3 scripts/validate_slippy_map.py <slippy-root>
python3 scripts/validate_slippy_map.py <slippy-root> --tiles-csv <tiles.csv>
```

The validator checks directory shape, optional image readability, and optional CSV alignment without importing RoboSat.
