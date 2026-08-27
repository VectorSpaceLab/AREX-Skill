# Troubleshooting

This page covers the predictable failures that show up while geocoding, querying Overpass, or loading local OSM XML.

## Quick symptom map

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `InsufficientResponseError` from `geocode` | Nominatim returned no match for the text query. | Make the query more specific, switch to a structured query, or inspect the candidate with `geocode_to_gdf`. |
| `InsufficientResponseError` from `geocode_to_gdf` | No OSM element matched, or the result set was empty. | Try `which_result=1`, a more specific query, or an explicit OSM ID lookup. |
| `TypeError: ... if by_osmid is True` | `by_osmid=True` was used with a non-string query. | Pass a string OSM ID such as `N...`, `W...`, or `R...`. |
| `TypeError: ... geometry of type (Multi)Polygon` | A place query resolved to a point or non-polygon geometry. | Use the address workflow instead, or pick a different `which_result`. |
| `ValueError: The geometry of polygon is invalid` | The supplied polygon is self-intersecting or otherwise invalid. | Fix or dissolve the geometry first, or derive it from `geocode_to_gdf(...).union_all()`. |
| `TypeError: Geometry must be a shapely Polygon or MultiPolygon` | A wrong geometry type was passed into a polygon workflow. | Pass a Polygon/MultiPolygon only, in `EPSG:4326`. |
| `InsufficientResponseError: No matching features` | The tags are too narrow, the geometry misses the target, or the XML lacks the needed members. | Broaden the tags, widen the boundary, or inspect the local XML source. |
| `CacheOnlyInterruptError` | `settings.cache_only_mode=True` deliberately stopped after saving the response. | Rerun with `cache_only_mode=False` if you want the assembled graph or GeoDataFrame. |
| HTTP `429` or `504`, or repeated pauses | Public Nominatim/Overpass rate limiting or a large query. | Keep rate limiting enabled, shrink the query area, reuse cache, or self-host the API. |
| `ImportError` during `graph_from_point(..., dist_type="network")` | Nearest-node search needs the optional neighbor-search dependency set. | Install the optional nearest-neighbor extras or switch to `dist_type="bbox"`. |
| `graph_from_xml` warns that the XML appears to be OSMnx-generated | That input path is not the intended XML source for this function. | Use raw OSM XML for acquisition, or route saved-graph persistence to `graph-modeling-io`. |
| Local XML has missing or clipped relations | The extract is incomplete, so some relation geometry cannot be rebuilt. | Use a less-clipped source extract, a larger query, or accept that some features may be missing. |

## Fast recovery steps

1. Check the coordinate order first.
   - bbox: `(left, bottom, right, top)`.
   - point: `(lat, lon)`.
2. Check the geometry type next.
   - Graph/feature polygon workflows need valid Polygon or MultiPolygon inputs.
3. Check the query semantics.
   - `tags` are unioned.
   - `custom_filter` strings intersect; lists union.
4. Check the service and cache controls.
   - Keep `use_cache=True` for repeatable runs.
   - Keep `overpass_rate_limit=True` for public services.
   - Use `cache_only_mode=True` only when you really want cache warming.
5. Check the result expectation.
   - A valid query can still return nothing if the tags are too narrow or the place has no polygon boundary.

## Public-service reminders

- Do not use concurrency to try to bypass public Overpass limits.
- Do not disable rate limiting on public endpoints just to make a query return faster.
- If you need many large queries, plan for caching or a self-hosted Overpass instance.

## XML-specific reminders

- `graph_from_xml` is for local raw OSM XML acquisition, not for persisted OSMnx graphs.
- `features_from_xml` can be more forgiving with clipped extracts, but missing relation members can still reduce the final result set.
- If the XML source is already known to be incomplete, prefer a wider raw extract over a clipped one.
