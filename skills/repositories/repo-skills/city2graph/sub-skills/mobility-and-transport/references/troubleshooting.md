# Troubleshooting and validation

Use the symptom, evidence, and recovery action together. Do not hide warnings
that change graph meaning; retain them with the run record.

## OD graphs

| Symptom | Likely cause | Recovery |
|---|---|---|
| `zones_gdf must be a GeoDataFrame` | A regular DataFrame or invalid geometry container was passed | Construct a real GeoDataFrame with a `geometry` column and a declared CRS. |
| `zone_id_col ... not found`, null IDs, or duplicate IDs | The zone ID contract is incomplete | Pass the correct column, or set `zone_id_col=None` only when the index is the intended unique ID space. |
| `No overlapping zone IDs` | All edge endpoints or all matrix labels are outside the zone set | Inspect ID dtype/casing and the intersection before retrying; do not accept an empty graph as a successful join. |
| Unknown endpoint warning | Some edge-list rows refer to zones absent from `zones_gdf` | Fix the upstream join or explicitly document the dropped rows. The function keeps only valid endpoints. |
| Adjacency label/order warning | Labeled matrix and zone IDs only partially overlap, or a NumPy array has implicit order | Prefer a labeled DataFrame; for an array, reorder zones to the exact row/column order before calling. |
| `Adjacency DataFrame must be square` or index/columns mismatch | Matrix structure is not a square labeled adjacency matrix | Make index and columns equal, unique, and in the same order. |
| `Adjacency ndarray size must match` | Array dimensions do not equal the number of zones | Fix the array or zone frame; an array has no labels for the function to recover. |
| Multi-weight `threshold_col` error | More than one `weight_cols` value was supplied without a valid primary | Choose a threshold/canonical column from `weight_cols`. |
| Non-numeric weight error | A weight column is all text or mixed with uncoercible values | Clean the column. Existing NaN is converted to zero with a warning; invalid text is not silently discarded. |
| Unexpectedly empty edges | No-threshold mode keeps only `weight > 0`; self-loops are dropped by default; a threshold is inclusive but may remove all rows | Inspect post-aggregation weights, self-loop policy, `threshold`, and `threshold_col`. Empty edges still retain a canonical schema. |
| Reciprocal edges appear once | `directed=False` intentionally merges them | Use `directed=True` for oriented flows. In undirected mode weights are summed before thresholding and pair order is lexical by string form. |
| Edge geometry is null or edges disappear | `compute_edge_geometry=False`, missing zone geometry/centroid, or an empty input | Disable geometry for non-spatial analysis, or repair geometry/CRS. A missing centroid causes affected edges to be dropped with a warning. |
| Centroid/geographic accuracy warning | Zones use lon/lat or no CRS | Project to an appropriate metric CRS before centroid-based geometry if distances/positions matter. |

### OD smoke assertions

```python
assert nodes.index.is_unique
assert set(edges.index.names) == {"source", "target"}
assert "weight" in edges.columns
assert set(edges.index.get_level_values(0)) <= set(nodes.index)
assert set(edges.index.get_level_values(1)) <= set(nodes.index)
```

## Feed loading and DuckDB

| Symptom | Likely cause | Recovery |
|---|---|---|
| `SHOW TABLES` is empty after `load_gtfs` or `load_gbfs` | Wrong local path, empty archive/directory, malformed input, or a load exception | Check the path and logs, inspect the archive/JSON locally, and verify file suffixes. These functions do not fetch a replacement feed. |
| DuckDB spatial load/install failure | The `spatial` extension is not available in the environment/cache | Install or provision the extension in the controlled environment, then retry. Do not turn on unapproved network access merely to hide the prerequisite. |
| `travel_summary_graph` raises missing `stop_times`, `stops`, or `trips` | The feed is incomplete for a stop-level schedule graph | Load a complete GTFS snapshot or choose a GBFS/domain-specific workflow instead. |
| `stops must contain either a geometry column or both stop_lon and stop_lat` | Summary graph cannot create node/edge geometry | Add a DuckDB geometry column or valid coordinate columns before calling. `load_gtfs` creates geometry when coordinates are castable. |
| Geometry is unexpectedly null | One or both stop coordinates/geometries are null | Inspect stop rows and decide whether null geometry is acceptable; graph edges can still carry their weighted attributes where the query permits null geometry. |
| GBFS data is not in expected tables | The JSON structure is not one of the recognized collections, or a file stem collided | Inspect `SHOW TABLES`, JSON `data`, table columns, and row counts. `load_gbfs` is intentionally a shallow flattener, not a full GBFS relational model. |
| GBFS has no transit edges | Expected behavior | `load_gbfs` only loads local JSON. Build a station/vehicle graph from the resulting schema separately. |

## GTFS service dates and times

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Invalid calendar date format` | A calendar argument is not `YYYYMMDD` | Pass strings such as `20240101`; do not pass `2024-01-01`. |
| Calendar bound outside valid range or start after end | The requested window is inconsistent with feed dates | Inspect `calendar` and `calendar_dates`, then choose an inclusive in-range window. |
| Explicit date window rejected because no calendar tables exist | The package has no service evidence to expand | Add `calendar.txt`/`calendar_dates.txt`, or omit the window to use the fallback `sc=1` per service ID when summary construction permits it. |
| No legs from `get_od_pairs` without `calendar` | Without `calendar`, both `start_date` and `end_date` are required | Supply an explicit `YYYYMMDD` window; `calendar_dates` alone does not remove this API requirement. |
| Service unexpectedly absent/present on a date | `calendar_dates` exception semantics were overlooked | Type `1` adds a service date; type `2` removes it. Test the effective active dates rather than reading weekly flags alone. |
| `Invalid time format` | A bound is not `HH:MM:SS` or contains non-numeric components | Use exact three-part time strings. Numeric strings such as `"3600.0"` are not accepted. |
| Inverted time window | `start_time` is later than `end_time` in absolute seconds | Fix the bounds. For after-midnight GTFS service use extended hours such as `25:30:00`, not a wrapped `01:30:00`. |
| After-midnight legs have wrong dates | Extended hours were normalized before city2graph saw them | Preserve `HH:MM:SS` values above 24 hours. The package converts them to the following service date when building timestamps. |
| Summary frequency is larger than trip count | `use_frequencies=True` expanded headway services | Inspect `frequencies` and record whether frequency multipliers are intended. Set `use_frequencies=False` for one count per trip. |
| Summary frequency is zero or travel time non-positive | Invalid schedule times, no active service, or malformed stop sequence | Inspect active dates, stop sequence, departure/arrival values, and `frequency.headway_secs`; the summary intentionally filters non-positive travel times and inactive services. |

## Output and migration checks

- Default outputs are GeoDataFrame pairs, not NetworkX graphs. Inspect the
  pair before conversion.
- `get_od_pairs` uses a row-oriented table and does not return a MultiIndex;
  `travel_summary_graph` edges use `(from_stop_id,to_stop_id)`; non-empty OD
  graph edges use `(source,target)`. An empty OD edge result keeps its
  canonical endpoint columns and may have a plain empty index, so branch on
  `edges.empty` before consuming index levels.
- `as_nx` is deprecated in both graph builders. Prefer
  `city2graph.utils.gdf_to_nx(nodes=..., edges=..., directed=...)`; expect
  internal NetworkX node IDs and use `_original_index` to recover provider or
  zone IDs.
- A NetworkX graph with no edge geometry is valid when geometry was disabled;
  do not infer missing geometry from missing weights.
- If a graph is empty, distinguish an intentionally filtered result from a
  failed data join by checking tables, IDs, active dates, and warnings.

## Environment boundary

These workflows require an installed `city2graph` package and its core
geospatial/DuckDB dependencies. Transit graph geometry additionally requires
DuckDB spatial support. Verification should use tiny local fixtures or an
in-memory connection, not a live GTFS/GBFS endpoint. A missing network is not a
reason to invent feed contents, and successful local loading is not evidence
that a provider's live feed schema is stable.
