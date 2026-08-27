# Overture workflows

This reference contains practical, offline-first recipes for the data-ingestion
sub-skill. The public API is in `city2graph.data`; run the snippets in an
installed `city2graph` environment. The examples deliberately make the area,
types, CRS, release, and output policy explicit.

## Choose the acquisition shape

| Need | Input | Consequence |
| --- | --- | --- |
| Fast rectangular query | `[min_lon, min_lat, max_lon, max_lat]` | Overture bbox only; no exact irregular-boundary clip |
| Exact study polygon | `Polygon`/`MultiPolygon` in WGS84 | Bbox query followed by precise clipping |
| Existing geospatial table | first geometry of a `GeoSeries`/`GeoDataFrame` | Reprojects to WGS84 when its CRS is known and non-WGS84 |
| Human-readable place | `place_name="City, Country"` | Nominatim lookup, then first polygonal result |

`area` and `place_name` are mutually exclusive and exactly one is required.
Resolve a place once and save/inspect its polygon if reproducibility matters;
a future run should use the saved polygon rather than repeatedly geocoding.

## Reproducible bbox download with explicit layers

```python
from pathlib import Path
import city2graph as c2g

bbox = [-2.995, 53.395, -2.975, 53.415]  # WGS84 lon/lat
out = Path("./artifacts/overture/liverpool")

layers = c2g.load_overture_data(
    area=bbox,
    types=["building", "segment", "connector"],
    output_dir=str(out),
    prefix="liverpool_",
    save_to_file=True,
    return_data=True,
    # release="<currently advertised release>",
)

buildings = layers["building"]
segments = layers["segment"]
connectors = layers["connector"]
```

Use a release pin after checking the currently advertised catalogue. Do not
copy an example's historical release blindly: Overture keeps only recent
monthly releases, and a stale release may be rejected by the CLI even if local
validation could not reach the catalogue.

The files are named:

```text
artifacts/overture/liverpool/liverpool_building.geojson
artifacts/overture/liverpool/liverpool_segment.geojson
artifacts/overture/liverpool/liverpool_connector.geojson
```

If a directory contains previous outputs, inspect or archive them first. The
function creates the directory and can replace files with the same generated
names.

## Place-name workflow

```python
import city2graph as c2g

boundary = c2g.get_boundaries("Liverpool, UK", user_agent="my-city2graph-app/1.0")
# Inspect boundary.geometry.iloc[0] and boundary.crs before continuing.
polygon = boundary.geometry.iloc[0]

layers = c2g.load_overture_data(
    area=polygon,
    types=["building", "segment", "connector"],
    output_dir="./artifacts/overture/liverpool",
    prefix="liverpool_",
    return_data=True,
)
```

`get_boundaries` requests GeoJSON geometry and considers all returned
geocoding candidates, selecting the first polygon or multipolygon. It fails
with `ValueError` when there is no result or no polygon. A street address often
returns a point, so request a city, district, or administrative region instead.
Nominatim is a shared service: identify the application with `user_agent`, obey
its rate limits and policy, and cache the polygon when a run must be repeated.

For an offline or audited run, do not call Nominatim at all. Load a locally
reviewed polygon into a GeoDataFrame, ensure it has the correct CRS, and pass
its first geometry as `area`.

## Save-only and in-memory modes

### Save files, do not keep GeoDataFrames

```python
c2g.load_overture_data(
    area=bbox,
    types=["building", "segment"],
    output_dir="./artifacts/overture/query-001",
    prefix="query-001_",
    save_to_file=True,
    return_data=False,
)
# Public result is {}. Read the generated GeoJSON explicitly if needed.
```

This is useful when files are the handoff artifact. It does not mean that no
local read or rewrite happens: polygon queries and all segment layers are
postprocessed before their saved GeoJSON is finalized.

### Do not write files

```python
layers = c2g.load_overture_data(
    area=bbox,
    types=["building"],
    save_to_file=False,
    return_data=True,
)
```

The CLI's stdout is captured and parsed as GeoJSON. The parser starts at the
first `{` or `[` to tolerate warning text before a GeoJSON object. For a real
run, still treat an empty result as something to inspect rather than proof that
the area has no features.

For a no-network unit check, mock `city2graph.data.subprocess.run` and return a
small `FeatureCollection` in `stdout`; never substitute a live download for a
local test.

## Polygon clipping and segment context

A polygon query is implemented as a bbox download followed by exact local
processing. For buildings, places, and other non-segment layers, clipping uses
`geopandas.clip`. For segments, graph-aware clipping is used:

```python
layers = c2g.load_overture_data(
    area=study_polygon,
    types=["segment"],
    save_to_file=False,
    return_data=True,
    keep_outer_neighbors=False,
)
```

With the default `keep_outer_neighbors=False`, the segment network is strictly
cropped. With `True`, intersecting segments that cross the boundary are kept,
which is useful for context or boundary-aware network construction:

```python
layers = c2g.load_overture_data(
    area=study_polygon,
    types=["segment"],
    save_to_file=False,
    return_data=True,
    keep_outer_neighbors=True,
)
```

This option is accepted through `**kwargs`; it affects segment clipping only.
A bbox list does not provide an irregular clip geometry, so use a polygon when
exact boundary semantics matter.

After segment download, non-LineString geometries are dropped and
MultiLineStrings are exploded into LineString rows. When files are enabled,
the cleaned/clipped segment layer is written back to the same output path.

## Process a street network for graph construction

The Overture example workflow downloads layers, reprojects them to British
National Grid, filters to roads, then processes segments before morphology or
graph construction:

```python
import geopandas as gpd
import city2graph as c2g

buildings = gpd.read_file("./artifacts/overture/liverpool/liverpool_building.geojson")
segments = gpd.read_file("./artifacts/overture/liverpool/liverpool_segment.geojson")
connectors = gpd.read_file("./artifacts/overture/liverpool/liverpool_connector.geojson")

# Choose a projected CRS suitable for the study region.
target_crs = "EPSG:27700"
buildings = buildings.to_crs(target_crs)
segments = segments.to_crs(target_crs)
connectors = connectors.to_crs(target_crs)

# Overture segment contains many travel modes; select roads if that is the task.
if "subtype" in segments.columns:
    segments = segments.loc[segments["subtype"] == "road"].copy()

processed = c2g.process_overture_segments(
    segments,
    connectors_gdf=connectors,
    get_barriers=True,
    threshold=1.0,  # metres in EPSG:27700
)
```

The `subtype == "road"` filter is a workflow choice, not part of
`process_overture_segments`; keeping rail, water, paths, or other subtypes may
be correct for a multimodal task. Inspect available subtype values before
filtering.

The returned `processed` frame retains source columns and adds `length` and,
when enabled, `barrier_geometry`. Split pieces receive IDs like `source_1`,
`source_2`; the normalized `split_from` and `split_to` fractions identify their
source intervals.

## Connector metadata contract

Connector point locations are not recalculated from the point geometry. A
segment row must carry connector records in its `connectors` column, and the
connector GeoDataFrame must expose matching IDs:

```python
segments = gpd.GeoDataFrame(
    {
        "id": ["s1"],
        "connectors": [[
            {"connector_id": "c0", "at": 0.0},
            {"connector_id": "c1", "at": 0.5},
            {"connector_id": "c2", "at": 1.0},
        ]],
        "level_rules": [""],
    },
    geometry=[LineString([(0, 0), (100, 0)])],
    crs="EPSG:27700",
)
connectors = gpd.GeoDataFrame(
    {"id": ["c0", "c1", "c2"]},
    geometry=[Point(0, 0), Point(50, 0), Point(100, 0)],
    crs="EPSG:27700",
)
processed = c2g.process_overture_segments(
    segments,
    connectors_gdf=connectors,
    get_barriers=False,
    threshold=1.0,
)
```

A connector ID absent from `connectors_gdf["id"]` is ignored. Values can be
JSON strings, Python lists, or a single mapping; malformed values produce no
split rather than a hard error. The `at` value is a normalized fraction along
the source geometry, not a distance in CRS units.

## Barrier/passability workflow

```python
processed = c2g.process_overture_segments(
    segments,
    connectors_gdf=connectors,
    get_barriers=True,
)
passable = processed["barrier_geometry"]
```

Interpretation:

- no usable nonzero rule: passable geometry is the original line;
- `{"value": 1, "between": [0.2, 0.8]}`: remove the middle 60%, leaving two
  passable pieces;
- `{"value": 1}` with no `between`: entire segment is blocked and the value is
  `None`;
- `{"value": 0, ...}`: ignored, so it does not block;
- overlapping or touching intervals are treated as one covered range through
  the interval complement.

Keep `geometry` for the original network shape and use `barrier_geometry` only
where the downstream operation defines it as the passable/barrier-aware shape.
If a downstream function cannot accept `None`, handle blocked segments
explicitly rather than converting them to empty or zero-length lines silently.

## Local verification pattern

A safe test harness does not execute `overturemaps` or Nominatim:

1. Create a small WGS84 bbox and patch `city2graph.data.subprocess.run`.
2. Return a local GeoJSON FeatureCollection or point the mocked output path at
   a local temporary file.
3. Assert command flags, output path, dictionary keys, and clip behavior.
4. Build a tiny projected segment frame and connector frame in memory.
5. Assert split ordering, endpoint means, lengths, and passable barrier
   geometry.

This validates the city2graph transformation contract without asserting that an
external release, catalog, or service is currently reachable.
