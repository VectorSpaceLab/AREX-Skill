# Mapping and location workflows

This sub-skill covers the notebook-style workflows for maps, geocoding, routing, and geoenrichment. It assumes the caller already chose this sub-skill instead of the GIS admin, feature analysis, or imagery routes.

## 1) Environment and display boundaries

- Use the `arcgis-mapping` package with the installed `arcgis` package for map widgets and scenes.
- A successful Python import does not guarantee that a widget will render. The notebook or browser front end still matters.
- `Scene` display is especially front-end dependent; keep the user in a notebook-style environment if they want interactive 3D.
- When a notebook widget is not practical, use a local export path such as `Map.export_to_html(...)` or save the map or scene only if the user actually wants a persisted web item.

## 2) Web maps, web scenes, layers, symbols, renderers, and popups

### Create or open a map or scene

- `Map(item=...)` and `Scene(item=...)` open existing web map or web scene items.
- `Map(location=...)` and `Scene(location=...)` can start from a place name or location string.
- `Map.save(...)` and `Scene.save(...)` persist notebook work back to a web map or web scene item.
- `Map.update(...)` updates item metadata for an existing map item.
- `Map.export_to_html(...)` produces a local HTML artifact for sharing outside the notebook.

### Add, draw, and style content

- Use `Map.content.add(...)` when you want to add a layer, table, feature collection, or dataframe-like object with optional drawing and popup metadata.
- Use `Map.content.draw(...)` to place a geometry, feature set, or similar shape on the map with a popup, symbol, attributes, and title.
- Use `Map.content.renderer(index).smart_mapping()` to get smart-mapping helpers for a rendered layer.
- Smart mapping works on rendered layers. If the layer is not loaded or the map is not rendered, the styling step will not behave as expected.
- Common smart-mapping patterns include class breaks, unique values, heatmaps, dot density, predominance, relationship, and univariate color-size styling.

### Symbols and popups

- Use the symbol dataclasses from `arcgis.map.symbols` for custom map display:
  - `SimpleMarkerSymbolEsriSMS`
  - `SimpleLineSymbolEsriSLS`
  - `SimpleFillSymbolEsriSFS`
  - `PictureMarkerSymbolEsriPMS`
- Use `PopupInfo` and the popup element classes when you want custom titles, field lists, media, or text in a popup.
- Keep popup and symbol work focused on display. If the ask becomes feature schema, layer editing, or data cleanup, route out of this sub-skill.

### Offline areas

- Use `Map.offline_areas` to manage offline map areas for a web map.
- Offline area creation usually needs the area geometry or extent, scale bounds, basemap details, and sometimes a `tile_services` list for vector tile basemaps.
- `enable_updates`, `refresh_schedule`, and `refresh_rates` are part of the offline area planning story.

## 3) Geocoding and custom geocoders

### Choose the geocoder source

- Start with `get_geocoders(gis)` to inspect the registered geocoders on a GIS.
- Use `Geocoder.fromitem(item)` when the geocoder is published as a service item.
- Use `Geocoder(location, gis=...)` when you have a geocoding service URL, especially for secure services tied to a GIS.

### Common operations

- `geocode(...)` is for one location per request.
- `batch_geocode(...)` is for a list of addresses.
- `reverse_geocode(...)` resolves the address at a point location.
- `suggest(...)` is for autocomplete-style queries.
- `analyze_geocode_input(...)` helps map input columns to a geocoding service schema.
- `geocode_from_items(...)` supports geocoding from item or layer inputs.

### Batch geocoding caveats

- Check `geocoder.properties.locatorProperties.MaxBatchSize` and `SuggestedBatchSize` before batching.
- Respect `for_storage` when the results are meant to be stored or reused beyond a transient display.
- Batch geocoding can consume credits and may have service-specific limits or terms.
- If the user wants custom geocoding behavior, clarify whether they need a custom locator, a secure service item, or a plain public URL.

## 4) Network analysis, routing, service areas, OD matrices, and VRP

### Pick the solver family

- Route sequencing and directions: `network.analysis.find_routes(...)` or `RouteLayer.solve(...)`.
- Service areas: `network.analysis.generate_service_areas(...)` or `ServiceAreaLayer`.
- Closest facilities: `network.analysis.find_closest_facilities(...)` or `ClosestFacilityLayer`.
- OD cost matrices: `network.analysis.generate_origin_destination_cost_matrix(...)` or `ODCostMatrixLayer`.
- Location allocation: `network.analysis.solve_location_allocation(...)`.
- Vehicle routing: `network.analysis.solve_vehicle_routing_problem(...)`.

### Input and parameter discipline

- Most hosted network solvers expect `FeatureSet` inputs for stops, facilities, incidents, orders, depots, demand points, and barriers.
- Validate required fields and geometry before asking for a solve.
- Pay special attention to `travel_mode`, `impedance`, `measurement_units`, `time_of_day`, `time_zone_for_time_of_day`, and any time-window flags.
- Route and VRP work often depends on time zones and valid network locations. Do not assume the solver can infer those safely.
- Use `ignore_invalid_locations` and `locate_settings` only after you have decided how missing or snapped locations should be handled.
- If the user wants optimized sequencing, the solver may need explicit `reorder_stops_to_find_optimal_routes`, `preserve_terminal_stops`, or route-order settings.

### Output and cost awareness

- These solvers are remote service operations and can consume credits.
- Some calls can return route layers, directions, or feature sets, depending on the solver and the `future`/output options.
- If there is no network-analysis service available, do not pretend the solve can be completed locally. Validate the inputs and explain the service requirement instead.

## 5) Geoenrichment and reports

### Choose the enrichment source

- Use `Country(iso3, gis=...)` to work with country-specific data and discovery helpers.
- `Country.data_collections`, `Country.reports`, and `Country.subgeographies` are discovery helpers.
- Use `get_countries(gis=...)` to see which countries are available from the active source.
- Geoenrichment can come from a configured Web GIS or from ArcGIS Pro with Business Analyst and local data.

### Core enrichment patterns

- Use `enrich(...)` for study areas, data collections, and analysis variables.
- Use `Country.enrich(...)` when you are already working through a country object.
- `BufferStudyArea(...)` is useful when the study area should be buffered before enrichment or reporting.
- `standard_geography_query(...)` discovers named statistical areas before enrichment.
- `create_report(...)` produces PDF or Excel-style reports for a study area.
- `interesting_facts(...)` and `service_limits(...)` are discovery helpers when you need to understand service capabilities or limits.

### Enrichment caveats

- `study_areas` can be addresses, geometries, points, polygons, dataframes, or helper objects, depending on the exact API path.
- `data_collections` and `analysis_variables` are IDs, not free-form labels.
- `proximity_type`, `proximity_value`, and `proximity_metric` matter when enriching around points or lines.
- Report generation and enrichment are service-backed and may consume credits.
- If the user only needs a quick local sanity check, validate the study-area shape and requested variables first instead of trying a live report run.

## 6) Handoff rules

- If the request moves into portal ownership, sharing, cloning, or delete operations, hand off to the GIS admin/content sub-skill.
- If the request becomes feature-layer schema, dataframe, or editing work, hand off to the feature analysis sub-skill.
- If the request becomes raster or imagery analysis, hand off to the imagery sub-skill.
