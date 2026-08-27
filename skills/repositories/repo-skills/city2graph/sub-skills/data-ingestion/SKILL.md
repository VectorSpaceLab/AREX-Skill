---
name: data-ingestion
description: "Use city2graph Overture Maps acquisition, boundary resolution,
  clipping, output control, and segment preprocessing safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Overture data ingestion

Use this sub-skill when a workflow needs to resolve a place or area, acquire a
selected Overture Maps layer, save or return GeoJSON, clip an Overture query,
or prepare Overture transportation segments for graph or morphology work.
The public entry points are `city2graph.data.get_boundaries`,
`city2graph.data.load_overture_data`, and
`city2graph.data.process_overture_segments`.

This route teaches the `city2graph` 1.0.0 data surface. It is deliberately
separate from morphology and graph-conversion routes: it gets spatial inputs
into trustworthy GeoDataFrames and makes segment geometry usable, but it does
not construct the final graph.

## Route here when

- The input is an Overture bounding box, polygon, GeoSeries, GeoDataFrame, or
  a place name to be geocoded with Nominatim.
- You need the Overture CLI download options, release selection, STAC behavior,
  timeout flags, file naming, return semantics, or clipping behavior.
- You need to split Overture segments at connector positions, cluster nearby
  segment endpoints, calculate lengths, or derive passable geometries from
  `level_rules`.
- You need a safe, offline-verifiable acquisition plan rather than an agent
  silently making a live download.

## Route elsewhere / do not claim

- Build the morphology or heterogeneous graph after ingestion: use the
  morphology or graph-conversion sub-skills.
- Use Overture schema internals, raw Parquet/STAC implementation details, or
  undocumented CLI features as if they were `city2graph` contracts.
- Treat live Overture, AWS, or Nominatim access as a required verification
  step. Network access is an explicit runtime prerequisite and is not needed
  for the local preprocessing verification described here.
- Treat `barrier_geometry` as a literal barrier line. It is the *passable*
  remainder of the source segment after level-rule intervals are removed.

## Operating contract

### Public signatures

The installed package exposes these signatures:

```python
from city2graph.data import (
    get_boundaries,
    load_overture_data,
    process_overture_segments,
)

get_boundaries(place_name: str, user_agent: str = "city2graph")

load_overture_data(
    area=None,
    place_name=None,
    types=None,
    output_dir=".",
    prefix="",
    save_to_file=True,
    return_data=True,
    release=None,
    connect_timeout=None,
    request_timeout=None,
    use_stac=True,
    **kwargs,
)

process_overture_segments(
    segments_gdf,
    get_barriers=True,
    connectors_gdf=None,
    threshold=1.0,
)
```

`load_overture_data` returns a dictionary keyed by requested type only when
`return_data=True`; with `return_data=False` its public result is `{}` even
when files are written successfully. `process_overture_segments` returns a
GeoDataFrame, while `get_boundaries` returns a one-row boundary GeoDataFrame.

### Required area/place choice

`load_overture_data` requires **exactly one** of `area` and `place_name`:

- both omitted: `ValueError("Exactly one of 'area' or 'place_name' must be provided")`;
- both supplied: the same `ValueError`;
- `area` supplied: use it directly after area normalization;
- `place_name` supplied: resolve it with `get_boundaries`, then use the first
  returned geometry.

Do not pass a place name and a fallback area together. If a caller wants a
stable, reviewable boundary, resolve the name once, inspect or persist the
returned polygon, and use that polygon for a subsequent run.

### Area forms and CRS

Accepted `area` forms are:

- a four-value bounding box `[min_lon, min_lat, max_lon, max_lat]`, in WGS84;
- a Shapely `Polygon` or `MultiPolygon`, assumed to be in WGS84;
- a `GeoSeries` or `GeoDataFrame`; the first geometry is used, and a CRS other
  than WGS84 is reprojected to EPSG:4326 before the query.

A polygon or multipolygon becomes both a bounding-box query and a precise
clipping geometry. A four-value list becomes only a bounding-box query. For a
GeoSeries/GeoDataFrame with no CRS, the code does not invent one; assign the
correct CRS before calling it. The Overture query box is formatted as
`minx,miny,maxx,maxy`, with polygon bounds rounded to ten decimal places.

`WGS84_CRS` is the module constant `"EPSG:4326"`. Overture download coordinates
are geographic, but segment length and endpoint thresholds should normally be
computed after reprojecting the returned layers to a suitable projected CRS.

## Resolve a place boundary

`get_boundaries("Liverpool, UK")` calls Nominatim with:

```python
Nominatim(user_agent="city2graph").geocode(
    place_name,
    geometry="geojson",
    exactly_one=False,
)
```

It examines all returned locations and chooses the first result whose raw
GeoJSON geometry is `Polygon` or `MultiPolygon`; it does not blindly accept
the first geocoder result. The result is a WGS84 GeoDataFrame with one
`place_name` property. It raises `ValueError` when no result exists or no
polygon boundary is present; for a street address or point-only result, try a
more specific administrative region or a saved polygon instead. Set a
meaningful `user_agent` for a real Nominatim deployment and respect that
service's usage policy and rate limits.

## Select Overture layers

`types=None` requests all valid types. For reproducibility, pass an explicit
list and record the chosen release and area. The exact accepted type names are:

| Type | Typical feature role |
| --- | --- |
| `address` | Address features and street-number attributes |
| `bathymetry` | Vectorized bathymetry products |
| `building` | Building outer footprints |
| `building_part` | Parts associated with parent buildings |
| `division` | Official or non-official geographic divisions |
| `division_area` | Division land or maritime areas |
| `division_boundary` | Shared division boundaries |
| `place` | Points of interest such as schools, businesses, and landmarks |
| `segment` | Travel paths such as road, rail, or water LineStrings |
| `connector` | Transportation-network connector points |
| `infrastructure` | Infrastructure such as towers, lines, piers, and bridges |
| `land` | Land surfaces derived from coastlines |
| `land_cover` | Derived land-cover products |
| `land_use` | Human-use classifications |
| `water` | Inland and ocean water surfaces |

An unrecognized type raises `ValueError` before the CLI loop. There is no
`transportation` type in this validation set; use `segment` and `connector`
for the network workflow. The `place` Overture type is different from the
`place_name` geocoding argument.

## Download, file, and return controls

`load_overture_data` shells out once per requested type to the `overturemaps`
executable. The effective command starts like this:

```text
overturemaps download --bbox=min_lon,min_lat,max_lon,max_lat -f geojson --type=building
```

The `overturemaps` CLI must be installed and available on `PATH`. A non-zero
CLI exit raises `subprocess.CalledProcessError`; do not hide it as an empty
layer.

### Output matrix

- `save_to_file=True` (default) creates `output_dir` with
  `parents=True, exist_ok=True` and requests
  `<output_dir>/<prefix><type>.geojson` via `-o`.
- `return_data=True` (default) reads or parses each layer and returns it under
  its type key.
- `save_to_file=False` omits `-o`, captures CLI stdout, and parses GeoJSON
  from the first `{` or `[` in stdout. This tolerates warning text before the
  JSON, but an empty/non-JSON stdout becomes an empty WGS84 GeoDataFrame.
- `return_data=False` returns `{}`. With a saved polygon query or a saved
  `segment` layer, postprocessing can still read, clip/filter, and rewrite the
  file before returning; it is not a promise that no local read occurs.

For safe output handling, use a dedicated pre-existing or purpose-built output
folder, an explicit prefix, and expected type names. The function constructs
filenames by direct string concatenation and can overwrite an existing CLI
output or rewrite a postprocessed GeoJSON. Do not place secrets or unrelated
files in that directory, do not use an untrusted prefix/path, and record the
exact output paths before a run. If an existing file must be preserved, copy or
rename it first. `save_to_file=False` is the safer choice for an exploratory,
mocked, or intentionally ephemeral call.

Optional download controls are passed to the CLI as follows:

- `release="YYYY-MM-DD.N"` adds `-r release`.
- `connect_timeout` adds `--connect_timeout`; `request_timeout` adds
  `--request_timeout`.
- Timeout values are rounded to whole seconds because the CLI parses these
  flags as integers. `request_timeout` is ignored by the implementation on
  non-Windows/non-macOS systems according to the API documentation.
- `use_stac=True` is the default. `use_stac=False` adds `--no-stac` and can be
  a useful fallback when the STAC-geoparquet path is unavailable.
- `keep_outer_neighbors` is accepted through `**kwargs` and affects segment
  clipping only; its default is `False`.

## Releases and network caveats

When `release` is supplied, `city2graph` iterates the Overture Maps
`ALL_RELEASES` catalogue. If the catalogue is reachable and the requested
release is not advertised, it raises `ValueError` and lists the advertised
values. Overture retains only the most recent monthly releases, so do not
assume an old release remains downloadable; pin a currently advertised
release and record it with the result.

`ALL_RELEASES` is lazy in the installed Overture dependency. If catalogue
access fails, `city2graph` logs a warning and skips local validation rather
than rejecting the release; the CLI may still reject it. This warning is not
proof that the release exists. A live download also depends on DNS, network
access, the Overture/AWS service, and a working CLI installation. Use mocked
subprocess/HTTP boundaries and local GeoDataFrames for runtime skill checks;
do not require a live download to verify this sub-skill.

## Clipping and segment-layer cleanup

For a Polygon/MultiPolygon/geometry area, the function first downloads the
area's bounding box, then applies the precise geometry:

- non-segment types use `geopandas.clip`;
- `segment` uses `city2graph`'s graph-aware clipping path, with
  `keep_outer_neighbors=False` by default and `True` retaining segments that
  intersect the boundary;
- `MultiLineString` segment geometries are exploded;
- segment rows whose geometry is not `LineString` or `MultiLineString` are
  removed; the result index is reset.

The precise clipping geometry is not used for a bare list bbox, so a bbox
query can include features outside any intended irregular boundary. If exact
boundary containment matters, pass a polygon. Segment clipping is a network
operation, not merely a visual crop: choose `keep_outer_neighbors=True` when
boundary-crossing outer links are needed to maintain context, and inspect the
result before graph construction.

When a saved layer is polygon-clipped or is a segment layer, the postprocessed
GeoDataFrame is written back to the same `<prefix><type>.geojson` path. This
can change geometry and row count compared with raw CLI output.

## Process Overture segments

Call `process_overture_segments` after loading the segment and connector layers,
and usually after reprojecting both to the same projected CRS:

```python
segments = segments.to_crs("EPSG:27700")
connectors = connectors.to_crs(segments.crs)
processed = process_overture_segments(
    segments,
    connectors_gdf=connectors,
    get_barriers=True,
    threshold=1.0,
)
```

The input is copied. An empty input is returned immediately unchanged (so no
new `length` or `barrier_geometry` columns are added). For a non-empty input,
the operation order is:

1. Warn if the segment CRS is missing or exactly EPSG:4326. The function does
   not reproject for you.
2. Ensure `level_rules` exists and replace null values with `""`.
3. Split rows using connector positions stored in each segment's `connectors`
   attribute, when a non-empty `connectors_gdf` is supplied.
4. Cluster/snap eligible endpoints when connectors are supplied.
5. Add `length = geometry.length`.
6. If `get_barriers=True`, add `barrier_geometry`.

The returned rows preserve copied source attributes and the segment CRS. For a
normal non-empty result, expect `length`; expect `barrier_geometry` only when
barrier generation is enabled; expect `split_from`/`split_to` when at least one
row was actually split.

### Projected CRS is a correctness requirement

`length` is the GeoPandas/Shapely planar length in the current CRS units, and
`threshold` is also interpreted in current CRS units. In EPSG:4326 these are
degrees, not meters, and the function emits a warning. Reproject segments and
connectors to a locally appropriate projected CRS (for example EPSG:27700 for
the Liverpool example) before processing. Do not compare a threshold of `1.0`
across geographic and projected inputs as though it represented the same
physical distance. The function does not harmonize connector CRS or validate
that connector geometry matches the segment CRS; make them match yourself.

### Connector splitting and endpoint clustering

`connectors_gdf` must be a GeoDataFrame with an `id` column. Connector point
geometry is not used to locate the split: each segment's `connectors` metadata
provides records such as:

```python
[{"connector_id": "c1", "at": 0.25},
 {"connector_id": "c2", "at": 0.75}]
```

Connector metadata may already be a list, a JSON-like string, or a single
mapping. Invalid JSON, non-dict records, missing IDs, and missing `at` values
are ignored. Only IDs present in `connectors_gdf["id"]` are used. The
implementation expects `at` to be a normalized fraction along the line in
`[0, 1]`; it sorts and deduplicates supplied values and combines them with the
endpoints `0.0` and `1.0`, but does not validate or clamp out-of-range values.
The geometry is split using normalized line substrings. If a source row has
multiple pieces,
its `id` becomes `<original_id>_1`, `<original_id>_2`, and so on (or uses the
source index if no `id` column exists); `split_from` and `split_to` record each
fraction. Source attributes are repeated on each piece. Empty split pieces are
dropped. With no usable connector records, the original row remains intact.

After splitting, endpoint clustering applies only to non-empty LineStrings.
Endpoints are assigned to rounded x/y bins of width `threshold`; endpoints in
the same bin are replaced by their coordinate mean. This is a fast grid-bin
operation, not a full pairwise distance clustering algorithm, so the threshold
must be a positive, meaningful unit in the projected CRS and bin-boundary
behavior should be checked on sensitive networks. Only first and last
coordinates change; interior vertices are preserved. Non-LineString rows and
an input containing no eligible lines pass through this step unchanged.

### Barrier/passability geometry

The default `get_barriers=True` interprets `level_rules` records. A nonzero rule
with no `between` interval means the entire segment is blocked and yields
`None` in `barrier_geometry`. A nonzero rule with `between: [start, end]`
removes that normalized interval; the complement is emitted as a LineString
when one passable piece remains, a MultiLineString when multiple pieces remain,
or `None` when no passable interval remains. Overlapping and touching intervals
are handled by the sorted complement calculation. A rule with `value == 0`,
malformed JSON, a non-dict rule, or a short/missing `between` array is ignored;
ignored or empty rules leave the original geometry as the passable geometry. A
two-value `between` array is converted with `float`, so non-numeric interval
values can raise and should be validated upstream. Interval values are expected
to be normalized to `[0, 1]`; the implementation does not clamp them. Missing
or null `level_rules` are normalized to an empty string.

Use `barrier_geometry` as the geometry to pass to later accessibility,
tessellation, or routing logic when that later workflow expects passable road
space. Keep the original `geometry` if you need the unmodified segment shape.
A `None` barrier geometry is meaningful blocked data, not a download failure.

## Safe, offline-first verification

Do not verify this route by downloading Overture data or geocoding a live place.
Use a synthetic WGS84 bbox with `subprocess.run` mocked, or parse a local
GeoJSON string/file fixture. Verify at minimum:

- both omitted and both supplied area/place inputs raise `ValueError`;
- an explicit valid type builds the expected mocked CLI command, while an
  invalid type fails before download;
- `save_to_file`, `return_data`, prefix, release, timeout, and `use_stac`
  flags have the documented matrix behavior;
- a mocked polygon result is clipped and a mocked segment result keeps only
  LineStrings and explodes MultiLineStrings;
- a synthetic projected segment with connector positions produces ordered
  split IDs and `split_from`/`split_to` values;
- endpoint clustering changes only eligible endpoints and leaves interior
  vertices unchanged;
- partial, full, zero-valued, malformed, and overlapping level rules produce
  the expected passable geometry or `None`;
- an empty segment frame remains unchanged, and a geographic/no-CRS frame
  warns about projected CRS.

These checks should use local fixtures and mocks. A passing mocked check proves
command construction and local transformation behavior, not that the current
Overture release, CLI, Nominatim service, or network endpoint is available.
