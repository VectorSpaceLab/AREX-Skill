---
name: data-acquisition
description: "Acquire OSMnx graphs, features, geocodes, and local OSM XML with
  query-geometry selection, custom tags/filters, cache and rate-limit controls,
  and historical Overpass snapshots."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Acquisition

Use this route when the user wants to fetch OpenStreetMap data, plan a query, or recover data from a local OSM XML file.

## Covers

- `geocode` and `geocode_to_gdf`
- `graph_from_bbox`, `graph_from_point`, `graph_from_address`, `graph_from_place`, `graph_from_polygon`, `graph_from_xml`
- `features_from_bbox`, `features_from_point`, `features_from_address`, `features_from_place`, `features_from_polygon`, `features_from_xml`
- `settings` for Nominatim, Overpass, caching, timeouts, headers, `cache_only_mode`, and historical snapshots
- OSM tag dictionaries and graph `custom_filter` strings/lists
- local OSM XML fallback from downloaded `.osm`, `.bz2`, or `.gz` files

## Route elsewhere

- Graph validation, conversion, projection, simplification, and persistence → `graph-modeling-io`
- Nearest-node/edge matching, routing, travel time, and stats → `routing-analysis`
- Plotting downloaded data → `elevation-visualization`

## Start here

1. Choose the query geometry.
   - bbox = `(left, bottom, right, top)` in EPSG:4326.
   - point = `(lat, lon)` plus `dist` meters.
   - address = geocode an address to a point, then query around it.
   - place = geocode to a Polygon/MultiPolygon boundary.
   - polygon = already have a valid Shapely Polygon or MultiPolygon.
   - xml = local OSM XML fallback when the data is already downloaded.
2. Choose the output family.
   - Graph queries return `nx.MultiDiGraph`.
   - Feature queries return a GeoDataFrame indexed by `element` and OSM ID.
   - Geocoding returns either `(lat, lon)` or a place/element GeoDataFrame.
3. If you need a historical snapshot, set the Overpass date in `settings.overpass_settings` before querying.
4. If you only need a plan, run [scripts/osmnx_query_template.py](scripts/osmnx_query_template.py) and do not hit the network.

## Common request patterns

- “Get streets around a point or address” → `graph_from_point` or `graph_from_address`.
- “Get streets for a neighborhood or city boundary” → `graph_from_place`.
- “Get building footprints, amenities, or transit stops” → `features_from_*`.
- “Resolve a place to a boundary or OSM ID” → `geocode_to_gdf`.
- “Use a local OSM extract” → `graph_from_xml` or `features_from_xml`.

## Query rules that matter

- `graph_from_point(..., dist_type="network")` uses nearest-node search after building the bbox graph. On an unprojected graph this needs the nearest-neighbor optional dependency set; use `dist_type="bbox"` if you want the simpler path.
- `graph_from_place` and `features_from_place` need the geocoder result to be a Polygon or MultiPolygon. If the place resolves to a point, use the address workflow or pass a better query / different `which_result`.
- `geocode_to_gdf(..., by_osmid=True)` expects a string OSM ID with an `N`, `W`, or `R` prefix.
- `which_result` is 1-based. For lists of queries, pass a matching list of `which_result` values.
- `features_from_*` tag dicts use union semantics: `True` = any value, `str` = one exact value, `list[str]` = any listed value.
- `custom_filter` for graph queries is different: a string means intersect those conditions; a list means union the alternatives.

## Expected outputs

- Graph builders should yield a graph in EPSG:4326 with `crs`, node `x`/`y`/`street_count`, and edge `osmid`/`length`.
- Feature builders should yield a nonempty GeoDataFrame when the query is valid and tags match. Empty or filtered-out results usually mean the query or tags were too narrow, not that acquisition failed.
- Local XML builders should work without network access and are the preferred fallback for already-downloaded OSM data.

## Read these next

- [references/workflows.md](references/workflows.md) for function-by-function recipes and parameter choices.
- [references/query-settings.md](references/query-settings.md) for Nominatim/Overpass/cache/header/date settings.
- [references/troubleshooting.md](references/troubleshooting.md) for empty responses, bad geometries, rate limits, and XML fallback failures.
- [scripts/osmnx_query_template.py](scripts/osmnx_query_template.py) to print a safe no-network query plan before making any live request.
