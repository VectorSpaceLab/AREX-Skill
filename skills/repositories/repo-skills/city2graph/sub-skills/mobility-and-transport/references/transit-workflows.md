# Transit workflows

The transportation module is deliberately local-file and local-connection
oriented. It loads GTFS ZIP members or GBFS JSON files into an in-memory
DuckDB connection; it never contacts a transit provider or discovers a live
feed URL.

## Load local feeds

### GTFS

```python
from city2graph.transportation import load_gtfs

con = load_gtfs("/data/provider_feed.zip")
print(con.execute("SHOW TABLES").fetchall())
```

`load_gtfs` creates an in-memory DuckDB database, attempts to install/load the
DuckDB `spatial` extension, registers the package's `time_to_seconds` UDF, and
reads every non-directory `*.txt` member into a table named from its basename.
Values are imported as strings. When `stops.txt` is present, it adds a
`geometry` column using `ST_Point(stop_lon, stop_lat)` wherever both
coordinates can be cast to numbers; invalid or blank coordinates remain null.
A malformed/unreadable archive is logged and returns a connection that may have
no tables, so inspect `SHOW TABLES` rather than assuming success.

The summary graph needs `stops`, `trips`, and `stop_times`. `stops` must contain
either a DuckDB `geometry` column or both `stop_lon` and `stop_lat`. `get_od_pairs`
needs at least `trips` and `stop_times`; geometry output additionally needs a
usable `stops.geometry` column. A feed with only a subset of these tables can
be loaded, but not every operation is valid.

### GBFS

```python
from city2graph.transportation import load_gbfs

con = load_gbfs("/data/gbfs_snapshot/")
print(con.execute("SHOW TABLES").fetchall())
```

`load_gbfs` recursively reads local JSON files and uses the JSON `data` member.
It flattens the first recognized collection under `stations`, `bikes`,
`vehicles`, `vehicle_types`, or `feeds`; otherwise it stores the `data` object
as a one-row table. Table names are lower-case file stems with hyphens changed
to underscores. If a resulting table has `lat` and `lon`, it adds a point
`geometry` where coordinates are numeric. A repeated file stem can replace an
earlier table, so inspect table names and row counts. GBFS loading does not
create `trips`, `stop_times`, or transit edges; use SQL or a separate domain
workflow to build a shared-mobility graph.

## Time and date conventions

GTFS schedule times are strings in `HH:MM:SS`. The package intentionally
supports hours beyond 24: `25:30:00` is 91,800 seconds and means 01:30 on the
following service date when converted to a timestamp. Do not normalize an
extended GTFS time with ordinary `datetime.strptime` before passing it to the
package. Bare numeric strings such as `"3600.0"`, empty strings, `"nan"`, and
`"None"` are invalid; numeric values supplied as numeric objects are accepted
by the internal converter, but a clean GTFS feed should use the GTFS string
format.

`get_od_pairs` uses `_timestamp` to pair a service date with departure and
arrival times. It drops rows whose timestamps cannot be parsed safely and
computes `travel_time_sec = arrival_ts - departure_ts`. Validate that the feed
has positive, ordered stop times; the summary query explicitly retains only
positive travel times.

Summary time filters use the same extended-hour convention:

- `start_time` is an inclusive lower bound on a leg's departure time;
- `end_time` is an inclusive upper bound on the next stop's arrival time; and
- an inverted window raises `ValueError` (use `25:30:00` rather than wrapping
  an after-midnight bound back to `01:30:00`).

Calendar arguments use `YYYYMMDD`, not ISO `YYYY-MM-DD`:

- `calendar_start` and `calendar_end` are inclusive;
- requested bounds must lie inside the feed's usable date range and start must
  not be after end;
- `calendar.txt` expands weekly flags over the requested window; and
- `calendar_dates.txt` exception type `1` adds service and type `2` removes it.

If a feed has `calendar_dates` but no `calendar`, the exception dates can define
the service window. If neither calendar table has usable dates, summary graph
construction falls back to one service count per `service_id` when no explicit
window is requested. Supplying an explicit date window without either table,
or outside the usable range, raises `ValueError`.

## Individual GTFS OD legs

```python
from city2graph.transportation import get_od_pairs

legs = get_od_pairs(
    con,
    start_date="20240101",
    end_date="20240131",
    include_geometry=True,
    directed=True,
)
```

The function pairs consecutive rows within each `trip_id`, ordered by numeric
`stop_sequence`, using `LEAD`. With `directed=True`, the original trip
orientation is preserved. With the default `directed=False`, each row is
canonicalized so `orig_stop_id <= dest_stop_id`; the departure and arrival
timestamps are swapped along with the endpoints when needed. This is
canonicalization, not deduplication: separate trips, dates, and repeated legs
remain separate rows.

The normal non-geometry columns are:

| Column | Meaning |
|---|---|
| `trip_id` | Source trip |
| `service_id` | Source service |
| `orig_stop_id` | Origin stop after direction policy |
| `dest_stop_id` | Destination stop after direction policy |
| `date` | Active service date as `YYYY-MM-DD` text |
| `departure_ts` | Parsed timestamp |
| `arrival_ts` | Parsed timestamp |
| `travel_time_sec` | Arrival minus departure in seconds |

With geometry enabled and stop geometries available, the result is a
GeoDataFrame with a `geometry` column, straight `LineString` stop-to-stop
geometries, and CRS `EPSG:4326`. With `include_geometry=False`, it is a plain
DataFrame. If `stop_times` or `trips` is missing, the function logs the
incomplete feed and returns an empty DataFrame. If a feed has no `calendar`,
both `start_date` and `end_date` are required, even when `calendar_dates` is
available; use an explicit one-day or bounded window in that case.

## Aggregated travel summary graph

```python
from city2graph.transportation import travel_summary_graph

nodes, edges = travel_summary_graph(
    con,
    start_time="07:00:00",
    end_time="10:00:00",
    calendar_start="20240101",
    calendar_end="20240131",
    directed=False,
    use_frequencies=True,
)
```

The function first ensures DuckDB spatial support and a `time_to_seconds` UDF,
then prepares stop geometry and service/frequency counts. It returns:

- `nodes`: all stop records from the feed, indexed by `stop_id`, with geometry
  in `EPSG:4326` when available; and
- `edges`: a GeoDataFrame indexed by `(from_stop_id, to_stop_id)` with a
  straight `geometry` line (possibly null) and at least:
  - `travel_time_sec`: service-count-weighted mean leg travel time;
  - `frequency`: total effective service traversals in the resolved date
    window.

Only consecutive stop pairs with non-null times and positive travel time are
aggregated. `directed=True` preserves oriented stop pairs. The default
`directed=False` canonicalizes and merges reciprocal pairs, sums their
frequencies, and recomputes the weighted mean travel time across both
orientations. Even with no edges, the node frame is returned and the edge frame
retains its schema.

### Frequency expansion

With `use_frequencies=True` (the default) and a `frequencies` table, each
frequency row contributes:

```text
max(1, floor((end_time - start_time) / headway_secs))
```

departures for its trip. Trips not represented by `frequencies` receive a
multiplier of one. The effective edge frequency is the active service-day
count multiplied by that trip multiplier. With `use_frequencies=False`, all
trips receive multiplier one. This is a scheduled-service summary, not a
real-time vehicle count or capacity estimate.

### NetworkX compatibility

`travel_summary_graph(..., as_nx=True)` is deprecated and emits a
`DeprecationWarning`. Prefer keeping the GeoDataFrame pair and calling the
shared converter:

```python
nodes, edges = travel_summary_graph(con, as_nx=False)
G = city2graph.utils.gdf_to_nx(nodes=nodes, edges=edges, directed=False)
```

The compatibility output follows shared converter conventions: internal
integer node IDs, original stop IDs in node `_original_index`, node `pos`,
graph CRS/`is_hetero` metadata, and edge `_original_edge_index`. Do not treat
those internal IDs as provider stop IDs.

## Transit validation recipe

Before using a summary graph, check:

```python
required = {"stop_times", "stops", "trips"}
loaded = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
assert required <= loaded
nodes, edges = travel_summary_graph(con, as_nx=False)
assert nodes.index.is_unique
if not edges.empty:
    assert (edges["travel_time_sec"] > 0).all()
    assert (edges["frequency"] > 0).all()
```

Record the feed snapshot path, loaded table names, stop geometry source, date
and time windows, `directed`, `use_frequencies`, and whether geometry/spatial
extension loading was verified. No live-network requirement is part of this
record.
