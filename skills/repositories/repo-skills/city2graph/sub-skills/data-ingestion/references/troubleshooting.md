# Data-ingestion troubleshooting

Use this guide before changing code or retrying a live request. Separate
local input/processing failures from external-service failures, and preserve
the original input and output paths while diagnosing.

## First triage

1. Confirm the installed package and imports:

   ```python
   import city2graph
   from city2graph import data
   print(getattr(city2graph, "__version__", "unknown"))
   print(data.WGS84_CRS)
   ```

2. For downloads, confirm the executable without downloading:

   ```bash
   command -v overturemaps
   overturemaps --help
   ```

3. Record the exact `area` form, requested types, release, output directory,
   prefix, CRS, and `return_data`/`save_to_file` settings.
4. Reproduce the local transformation with a synthetic GeoDataFrame or a
   mocked subprocess before investigating DNS, Nominatim, AWS, or the Overture
   catalogue.
5. Do not replace an external error with an empty GeoDataFrame without logging
   the error and the query metadata.

## Validation and argument errors

### `Exactly one of 'area' or 'place_name' must be provided`

`load_overture_data` requires exactly one selector. Both `None` and both
non-`None` are rejected. Resolve a place separately if a fallback geometry is
needed:

```python
boundary = get_boundaries("City, Country")
load_overture_data(area=boundary.geometry.iloc[0], types=["building"])
```

Do not use an empty list as a meaningful bbox. The implementation only checks
`None` for mutual exclusion; a malformed list may fail later while formatting
the bbox.

### `Invalid types: [...]`

The validated set is `address`, `bathymetry`, `building`, `building_part`,
`division`, `division_area`, `division_boundary`, `place`, `segment`,
`connector`, `infrastructure`, `land`, `land_cover`, `land_use`, and `water`.
There is no `transportation` entry. Use `segment` and `connector` for an
Overture transportation-network workflow.

`types=[]` is treated as false and therefore expands to all valid types. If no
download should occur, do not call the function with an empty list; select a
specific list at the caller.

## Place resolution failures

### `Place not found: '...'`

Nominatim returned no locations. Check spelling, country context, network
access, and service policy. Retry only after respecting rate limits. For a
repeatable or offline run, stop using `place_name`, load a reviewed local
polygon, and pass it as `area`.

### `No polygon boundary for '...'. Try an administrative region.`

All returned locations lacked Polygon/MultiPolygon GeoJSON. A point result is
not enough for a study area. Use a city, district, or administrative region,
or provide a polygon directly. The function searches all returned locations,
but only accepts polygonal raw GeoJSON.

### Geocoder seems to select the wrong city

The function takes the first polygonal result returned by Nominatim. Add
country/region context to the query, inspect the returned boundary, and cache
the chosen polygon. Do not assume the textual place name uniquely identifies a
boundary.

## CLI and network failures

### `FileNotFoundError: overturemaps`

The `overturemaps` executable is not on `PATH`. Install the compatible
Overture Maps CLI in the same environment or invoke the Python environment that
contains it. This is distinct from an empty data response.

### `subprocess.CalledProcessError`

The CLI exited non-zero. Preserve its command and stderr where available, then
check:

- bbox order and values are WGS84 `[min_lon, min_lat, max_lon, max_lat]`;
- the requested type is supported by the installed CLI/schema;
- the release is currently available;
- the Overture/AWS endpoint is reachable;
- output directory permissions and free disk space are sufficient;
- the CLI supports the requested timeout/STAC flags.

Try `use_stac=False` only as a targeted fallback for a STAC catalog failure,
not as a blanket fix. Do not catch the exception and claim success.

### Release validation warns that the catalogue is unreachable

`ALL_RELEASES` is lazy. If iteration cannot reach its catalogue,
`city2graph` logs a warning and lets the CLI attempt the requested release. The
warning means *local validation was skipped*, not that the release is valid.
Check the CLI result and record the unresolved release state. If the catalogue
is reachable and the release is not advertised, the function raises
`ValueError` before the download.

### Timeout flags do not behave as expected

`connect_timeout` and `request_timeout` are rounded with Python `round` and
passed as integer strings using the underscored CLI option names:
`--connect_timeout` and `--request_timeout`. On non-Windows/non-macOS systems,
`request_timeout` is documented as ignored by the CLI path. Use a positive,
whole-second value when diagnosing a timeout, and inspect the mocked command to
verify the flag before retrying a live call.

### Empty returned GeoDataFrame after a successful command

Possible causes include no features, missing/empty stdout in no-file mode,
an output file that was not created, a bbox miss, or a parser/CLI warning. Check
`returncode`, stdout/stderr, output-file existence, CRS, geometry count, and
query bounds. In `save_to_file=False` mode, city2graph starts parsing at the
first `{` or `[`, so warning text before a valid GeoJSON object is tolerated;
non-JSON output is not a valid data result.

## Output and file safety

### Files are missing

With `save_to_file=True`, expected names are
`<output_dir>/<prefix><type>.geojson`. The directory is created with
`parents=True, exist_ok=True`, but the function does not create a separate run
manifest. Confirm the exact string value of `output_dir` and `prefix`, and
remember that `return_data=False` intentionally returns `{}` rather than the
GeoDataFrames.

### Existing files changed or were overwritten

The CLI receives `-o` for every saved type. Polygon queries and all segment
layers are read, processed, and written back to the same path. This may replace
raw output with clipped or exploded output. Use a dedicated run directory and
prefix; archive existing files before retrying. Avoid untrusted prefixes and
paths because the filename is assembled directly from them.

### `return_data=False` was expected to avoid processing

It controls the public return dictionary, not all local work. If a saved
polygon query or segment layer needs postprocessing, the function reads and
rewrites the file before returning. If the goal is an in-memory dry run, use
`save_to_file=False, return_data=True` with a mocked CLI in tests.

### A polygon is not clipped as expected

A bare four-value bbox has no precise clip geometry. Pass a Polygon or
MultiPolygon, or a GeoSeries/GeoDataFrame with a first geometry. For a
GeoSeries/GeoDataFrame, verify the CRS before passing it: a known non-WGS84 CRS
is reprojected, but a missing CRS is not inferred. Non-segment layers use
`geopandas.clip`; segment layers use graph-aware clipping.

### Boundary-crossing segments disappeared

`keep_outer_neighbors=False` is strict for segment clipping. Use
`keep_outer_neighbors=True` to retain segments that intersect the boundary, then
inspect whether the extra context is appropriate for the downstream graph.
This argument is passed through `**kwargs` and does not change building/place
clipping.

## CRS, geometry, and length failures

### Warning: projected CRS recommended

`process_overture_segments` warns when its non-empty input has no CRS or exactly
EPSG:4326. The function does not reproject. Reproject segments and connectors
to the same local projected CRS before processing:

```python
segments = segments.to_crs("EPSG:27700")
connectors = connectors.to_crs(segments.crs)
```

`length` is planar length in CRS units and `threshold` uses the same units.
Degrees are not metres. A correct-looking numeric output in EPSG:4326 can still
be physically wrong.

### Wrong location after area normalization

A raw Shapely Polygon is assumed to be WGS84 because it carries no CRS. A
GeoDataFrame/GeoSeries with a non-WGS84 CRS is reprojected to WGS84, but only
the first geometry is used. Ensure the geometry's declared CRS is truthful and
that the collection is ordered as intended.

### Segment rows vanish after loading

For the `segment` type, city2graph keeps only `LineString` geometries and
explodes `MultiLineString` into LineStrings. Point and Polygon rows are removed.
This is intentional cleanup for the segment-processing route. Inspect the raw
CLI output separately if mixed geometries are expected.

## Processing and connector failures

### No segments were split

Check all of the following:

- `connectors_gdf` is not `None` and not empty;
- it has an `id` column;
- every desired connector record's `connector_id` is present in that column;
- each segment has a `connectors` column containing a list, JSON-like string, or
  mapping;
- each record has numeric `at` and `at` is a normalized fraction;
- the segment geometry is a valid non-empty LineString.

The point geometry in `connectors_gdf` does not locate a split; the `at` value
in the segment metadata does. Malformed JSON and non-dict records are ignored.
Positions are sorted/deduplicated and include 0 and 1, so endpoint-only
metadata does not create extra pieces.

### Split IDs or attributes look unexpected

When a source row is split, the public `id` values become
`<source-id>_<part-number>` and source attributes are duplicated on each piece.
`split_from`/`split_to` are normalized fractions, not CRS distances. If the
source has no `id` column, the source index is used to form the base ID. Result
rows are reset to a new integer index.

### Endpoint clustering joins too much or too little

The clustering implementation puts each endpoint into rounded x/y bins of
width `threshold` and replaces endpoints in the same bin with their mean. It is
not a full-radius nearest-neighbor clustering algorithm. Use a positive
threshold in projected units, inspect the result, and reduce it when unrelated
junctions merge. Be especially cautious around bin boundaries and when the
coordinate scale is geographic.

Only first and last coordinates of eligible non-empty LineStrings are changed;
interior vertices and non-LineString geometries are preserved. Endpoint
clustering runs whenever a non-empty connectors GeoDataFrame is supplied, even
if no segment was split.

### `threshold` raises or produces nonsense

A zero threshold causes division by zero or invalid binning; a negative or
geographic threshold is also semantically unsafe. Choose a positive physical
unit after projecting both layers. The API does not validate this for you.

### `length` or `barrier_geometry` is missing

An empty segment frame returns immediately unchanged, so no derived columns are
added. For non-empty input, `length` is always added. `barrier_geometry` is
added only when `get_barriers=True` (the default). A missing `level_rules`
column is created as empty strings; null values are normalized to empty strings.

## Barrier-rule failures

### Every passable geometry is `None`

A nonzero level rule without a `between` interval represents a full barrier.
An interval covering `[0, 1]` also removes the whole segment. Preserve those
`None` values as blocked segments and decide explicitly how the downstream graph
should handle them.

### A partial barrier did not remove the expected part

`between` values are normalized fractions along the line, not CRS distances.
They must be a two-value list. Nonzero intervals are complemented into passable
pieces; overlapping and touching intervals are merged by the complement
calculation. Inspect the rule after parsing and use a simple straight line to
check expected geometry before debugging a real network.

### Malformed or zero rules seem to do nothing

That is the defined fallback: malformed JSON, non-dict rules, short `between`
arrays, and rules with `value == 0` are ignored. Empty or ignored rules leave the
original geometry in `barrier_geometry`. Validate upstream Overture attributes
if silent fallback would be unsafe for the research question.

## Offline diagnostic harness

A minimal safe approach is:

```python
from unittest.mock import patch
import geopandas as gpd
from city2graph.data import load_overture_data

geojson = '{"type":"FeatureCollection","features":[]}'
result = type("Result", (), {"stdout": geojson, "returncode": 0})()

with patch("city2graph.data.subprocess.run", return_value=result) as run:
    layers = load_overture_data(
        area=[-74.01, 40.70, -73.99, 40.72],
        types=["building"],
        save_to_file=False,
        return_data=True,
    )
    assert "building" in layers
    assert run.call_args.args[0][0:2] == ["overturemaps", "download"]
```

Use a local synthetic GeoDataFrame for clipping and
`process_overture_segments`; patch Nominatim when testing boundary resolution.
This harness verifies argument validation, command construction, and local
parsing without a live download. Native repository tests remain a separate
verification phase and should not be silently replaced by this check.
