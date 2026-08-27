# API reference

## Tiles helpers

### `robosat.tiles.pixel_to_location(tile, dx, dy)`

- Converts a normalized pixel offset inside a tile into lon/lat coordinates.
- `dx` and `dy` must be in the closed interval `[0, 1]`.
- Useful when you need geographic positions for tile-relative geometry work.

### `robosat.tiles.fetch_image(session, url, timeout=10)`

- Fetches an image URL through an existing HTTP session.
- Returns a `BytesIO` object on success.
- Returns `None` on any request or decode failure.

### `robosat.tiles.tiles_from_slippy_map(root)`

- Walks a Slippy Map tree and yields `(mercantile.Tile, path)` pairs.
- Tile identity comes from the `z/x/y` path components, not the extension.
- The raw traversal follows filesystem directory order and should not be assumed to be stable; sort the results if order matters.
- The helper is used by the dataset wrappers and tile validation scripts.

### `robosat.tiles.tiles_from_csv(path)`

- Reads a line-delimited CSV of tile ids.
- Expected column order: `x,y,z`.
- Yields `mercantile.Tile` objects.

### `robosat.tiles.stitch_image(into, into_box, image, image_box)`

- Pastes a cropped region from one image into another image in place.
- Used by buffering and overlap logic.

### `robosat.tiles.adjacent_tile(tile, dx, dy, tiles)`

- Looks up an immediate neighbor tile in a tile mapping.
- Returns an RGB PIL image or `None` if the neighbor is missing.

### `robosat.tiles.buffer_tile_image(tile, tiles, overlap, tile_size, nodata=0)`

- Builds a buffered RGB composite centered on one tile.
- Uses neighboring tiles when available and fills missing borders with `nodata`.
- Output size is `tile_size + 2 * overlap` in each dimension.

## Dataset wrappers

### `robosat.datasets.SlippyMapTiles(root, transform=None)`

- Dataset for a single Slippy Map tree.
- Returns `(image, tile)` pairs.
- Caches the discovered tiles and sorts them before iteration so downstream data loading is more stable than raw filesystem traversal.

### `robosat.datasets.SlippyMapTilesConcatenation(inputs, target, joint_transform=None)`

- Dataset for multiple input trees plus one target tree.
- Asserts that every tree contains the same tile ids in the same order.
- Returns concatenated input tensors, the target mask, and the tile list.

### `robosat.datasets.BufferedSlippyMapDirectory(root, transform=None, size=512, overlap=32)`

- Dataset for buffered tiles with neighbor overlap.
- Returns `(image, torch.IntTensor([x, y, z]))`.
- Use `unbuffer(probs)` to strip overlap from a prediction tensor.

## Rasterization helpers

### `robosat.tools.rasterize.feature_to_mercator(feature)`

- Converts GeoJSON Polygon or MultiPolygon coordinates from EPSG:4326 to EPSG:3857.
- Yields mercator-space polygon geometries.

### `robosat.tools.rasterize.burn(tile, features, size)`

- Rasterizes one tile against a feature list into a `size x size` numpy mask.
- Intended for binary foreground/background masks.
- `rs rasterize` currently expects exactly two classes and two colors in the dataset config.

## OSM extraction helpers

### `robosat.osm.core.FeatureStorage(out, batch)`

- Buffers extracted features and writes GeoJSON chunks to disk.
- When the batch fills, it writes a new file with a unique suffix.
- Call `flush()` at the end to write the final partial batch.

### `robosat.osm.core.is_polygon(way)`

- Checks whether an OSM way is closed and has enough nodes to form a polygon.
- It is a shape prefilter, not a validity guarantee.

### `robosat.osm.building.BuildingHandler`

- Extracts building polygons from OSM ways.
- Filters out non-visible building tags such as construction, houseboat, and underground variants.

### `robosat.osm.parking.ParkingHandler`

- Extracts parking polygons from OSM ways.
- Filters out parking tags that are unlikely to appear in imagery.

### `robosat.osm.road.RoadHandler`

- Buffers supported highway ways into road polygons.
- Uses lane and width heuristics, with optional tag overrides.

## Config and color helpers

### `robosat.config.load_config(path)`

- Loads a TOML config into a dictionary.
- Use it for dataset and model config files.

### `robosat.config.save_config(attrs, path)`

- Serializes a dictionary back to TOML.
- Pass a writable file object if you call it directly.

### `robosat.colors.make_palette(*colors)`

- Builds a PIL palette from Mapbox color names.
- Used for paletted masks and visual inspection.

### `robosat.colors.color_string_to_rgb(color)`

- Converts `"r,g,b"` into `[r, g, b]` integers.

### `robosat.colors.continuous_palette_for_color(color, bins=256)`

- Builds a continuous palette from one named color.
