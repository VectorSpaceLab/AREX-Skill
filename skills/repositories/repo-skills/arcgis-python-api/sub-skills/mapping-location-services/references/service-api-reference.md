# Service API reference

This file captures the verified import surface and the most important signatures for map widgets, geocoding, network analysis, and geoenrichment.

## Verified imports

The inspection environment confirmed these modules:

- `arcgis.map`
- `arcgis.map.symbols`
- `arcgis.map.renderers`
- `arcgis.map.popups`
- `arcgis.map.offline_mapping`
- `arcgis.geocoding`
- `arcgis.network`
- `arcgis.network.analysis`
- `arcgis.geoenrichment`

The map widget surface depends on the installed `arcgis-mapping` package in addition to `arcgis`.

## Map and widget signatures

```python
Map(location: str | None = None, *, item: Item | str | None = None, gis: GIS | None = None, **kwargs) -> None
Scene(location: str | None = None, *, item: Item | str | None = None, gis: GIS | None = None, **kwargs) -> None
```

```python
Map.save(self, item_properties: dict[str, Any], thumbnail: str | None = None, metadata: str | None = None, owner: str | None = None, folder: str | None = None) -> Item
Map.update(self, item_properties: dict[str, Any] | None = None, thumbnail: str | None = None, metadata: str | None = None) -> bool
Map.export_to_html(self, path_to_file: str, title: str | None = None) -> bool
Scene.save(self, item_properties: dict[str, Any], thumbnail: str | None = None, metadata: str | None = None, owner: str | None = None, folder: str | None = None) -> Item
Scene.update(self, item_properties: dict[str, Any] | None = None, thumbnail: str | None = None, metadata: str | None = None) -> bool
```

```python
MapContent.draw(self, shape, popup=None, symbol=None, attributes=None, title: str | None = None) -> None
MapContent.add(self, item, drawing_info: dict | None = None, popup_info: PopupInfo = None, index: int | None = None, options: dict | None = None) -> None
RendererManager.smart_mapping(self) -> SmartMappingManager
```

```python
SmartMappingManager.class_breaks_renderer(...)
SmartMappingManager.unique_values_renderer(...)
SmartMappingManager.heatmap_renderer(...)
SmartMappingManager.dot_density_renderer(...)
SmartMappingManager.pie_chart_renderer(...)
SmartMappingManager.predominance_renderer(...)
SmartMappingManager.relationship_renderer(...)
SmartMappingManager.univariate_color_size_renderer(...)
```

```python
OfflineMapAreaManager.create(self, area: str | list | dict[str, Any], item_properties: dict[str, Any] | None = None, folder: str | None = None, min_scale: int | None = None, max_scale: int | None = None, layers_to_ignore: list[str] | None = None, refresh_schedule: str = 'Never', refresh_rates: dict[str, int] | None = None, enable_updates: bool = False, ignore_layers: list[str] | None = None, tile_services: list[dict[str, str]] | None = None, future: bool = False) -> Item | PackagingJob
OfflineMapAreaManager.list(self) -> list
OfflineMapAreaManager.update(self, offline_map_area_items: list | None = None, future: bool = False) -> dict | PackagingJob | None
```

## Symbol, popup, and form dataclasses

```python
SimpleMarkerSymbolEsriSMS(...)
SimpleLineSymbolEsriSLS(...)
SimpleFillSymbolEsriSFS(...)
PictureMarkerSymbolEsriPMS(...)
PopupInfo(...)
PopupElementFields(...)
PopupElementMedia(...)
PopupElementText(...)
```

Useful shape for custom display:

```python
MapContent.draw(shape, popup=PopupInfo(...), symbol=SimpleMarkerSymbolEsriSMS(...), attributes={...})
```

## Geocoding signatures

```python
geocode(address, search_extent=None, location=None, distance=None, out_sr=None, category=None, out_fields='*', max_locations=20, magic_key=None, for_storage=False, geocoder=None, as_featureset=False, match_out_of_range=True, location_type='street', lang_code=None, source_country=None)
reverse_geocode(location, distance=None, out_sr=None, lang_code=None, return_intersection=False, for_storage=False, geocoder=None, feature_types=None, location_top='street')
batch_geocode(addresses, source_country=None, category=None, out_sr=None, geocoder=None, as_featureset=False, match_out_of_range=True, location_type='street', search_extent=None, lang_code='EN', preferred_label_values=None, out_fields=None)
get_geocoders(gis)
suggest(text, location=None, category=None, geocoder=None, search_extent=None, max_suggestions=5, country_code=None, preferred_label_values=None, return_collections=True)
geocode_from_items(input_data, output_type='Feature Layer', geocode_service_url=None, geocode_parameters=None, country=None, output_fields=None, header_rows_to_skip=1, output_name=None, category=None, context=None, gis=None)
analyze_geocode_input(input_table_or_item, geocode_service_url=None, column_names=None, input_file_parameters=None, locale='en', context=None, gis=None)
```

```python
Geocoder(location, gis=None)
Geocoder.fromitem(item)
Geocoder.geocode(...)
Geocoder.batch_geocode(...)
Geocoder.reverse_geocode(...)
Geocoder.suggest(...)
```

Important notes:

- `reverse_geocode` expects a point-like location in `x, y` order.
- `batch_geocode` should be chunked to the geocoder’s batch limit when needed.
- `for_storage=True` should be used intentionally when results will be stored or reused.
- `get_geocoders(gis)` is the safe way to inspect registered geocoders before choosing a locator.

## Network analysis signatures

```python
find_routes(stops, measurement_units='Minutes', analysis_region=None, reorder_stops_to_find_optimal_routes=False, preserve_terminal_stops='Preserve First', return_to_start=False, use_time_windows=False, time_of_day=None, time_zone_for_time_of_day='Geographically Local', uturn_at_junctions='Allowed Only at Intersections and Dead Ends', point_barriers=None, line_barriers=None, polygon_barriers=None, use_hierarchy=True, restrictions=None, attribute_parameter_values=None, route_shape='True Shape', route_line_simplification_tolerance=None, populate_route_edges=False, populate_directions=True, directions_language='en', directions_distance_units='Miles', directions_style_name='NA Desktop', travel_mode='Custom', impedance='Drive Time', overrides=None, time_impedance='TravelTime', save_route_data=False, distance_impedance='Kilometers', output_format='Feature Set', save_output_na_layer=False, time_zone_for_time_windows='Geographically Local', gis=None, future=False, accumulate_attributes=None, ignore_network_location_fields=False, ignore_invalid_locations=True, locate_settings=None)
```

```python
generate_service_areas(facilities, break_values='5 10 15', break_units='Minutes', analysis_region=None, travel_direction='Away From Facility', time_of_day=None, use_hierarchy=False, uturn_at_junctions='Allowed Only at Intersections and Dead Ends', polygons_for_multiple_facilities='Overlapping', polygon_overlap_type='Rings', detailed_polygons=False, polygon_trim_distance=None, polygon_simplification_tolerance=None, point_barriers=None, line_barriers=None, polygon_barriers=None, restrictions=None, attribute_parameter_values=None, time_zone_for_time_of_day='Geographically Local', travel_mode='Custom', impedance='Drive Time', save_output_network_analysis_layer=False, overrides=None, time_impedance=None, distance_impedance=None, polygon_detail=None, output_type=None, output_format=None, gis=None, future=False, accumulate_attributes=None, ignore_network_location_fields=False, ignore_invalid_locations=True, locate_settings=None, exclude_sources_from_polygon_generation=None)
```

```python
find_closest_facilities(incidents, facilities, measurement_units='Minutes', analysis_region=None, number_of_facilities_to_find=1, cutoff=None, travel_direction='Incident to Facility', use_hierarchy=True, time_of_day=None, time_of_day_usage='Start Time', uturn_at_junctions='Allowed Only at Intersections and Dead Ends', point_barriers=None, line_barriers=None, polygon_barriers=None, restrictions=None, attribute_parameter_values=None, route_shape='True Shape', route_line_simplification_tolerance=None, populate_directions=False, directions_language='en', directions_distance_units='Miles', directions_style_name='NA Desktop', time_zone_for_time_of_day='Geographically Local', travel_mode='Custom', impedance='Drive Time', save_output_network_analysis_layer=False, overrides=None, save_route_data=False, time_impedance='TravelTime', distance_impedance='Kilometers', output_format='Feature Set', gis=None, future=False, accumulate_attributes=None, ignore_network_location_fields=False, ignore_invalid_locations=True, locate_settings=None)
```

```python
generate_origin_destination_cost_matrix(origins, destinations, travel_mode='Custom', time_units='Minutes', distance_units='Kilometers', analysis_region=None, number_of_destinations_to_find=None, cutoff=None, time_of_day=None, time_zone_for_time_of_day='Geographically Local', point_barriers=None, line_barriers=None, polygon_barriers=None, uturn_at_junctions='Allowed Only at Intersections and Dead Ends', use_hierarchy=True, restrictions=None, attribute_parameter_values=None, impedance='Drive Time', origin_destination_line_shape='None', save_output_network_analysis_layer=False, overrides=None, time_impedance=None, distance_impedance=None, output_format=None, gis=None, future=False, accumulate_attributes=None, ignore_network_location_fields=False, ignore_invalid_locations=True, locate_settings=None)
```

```python
solve_location_allocation(facilities, demand_points, measurement_units=None, analysis_region=None, problem_type=None, number_of_facilities_to_find=None, default_measurement_cutoff=None, default_capacity=None, target_market_share=None, measurement_transformation_model=None, measurement_transformation_factor=None, travel_direction=None, time_of_day=None, time_zone_for_time_of_day=None, uturn_at_junctions=None, point_barriers=None, line_barriers=None, polygon_barriers=None, use_hierarchy=True, restrictions=None, attribute_parameter_values=None, allocation_line_shape=None, travel_mode='Custom', impedance=None, save_output_network_analysis_layer=False, overrides=None, time_impedance=None, distance_impedance=None, output_format=None, gis=None, future=False, accumulate_attributes=None, ignore_network_location_fields=False, ignore_invalid_locations=True, locate_settings=None)
```

```python
solve_vehicle_routing_problem(orders, depots, routes, breaks=None, time_units='Minutes', distance_units='Miles', analysis_region=None, default_date=None, uturn_policy='ALLOW_DEAD_ENDS_AND_INTERSECTIONS_ONLY', time_window_factor='Medium', spatially_cluster_routes=True, route_zones=None, route_renewals=None, order_pairs=None, excess_transit_factor='Medium', point_barriers=None, line_barriers=None, polygon_barriers=None, use_hierarchy_in_analysis=True, restrictions=None, attribute_parameter_values=None, populate_route_lines=True, route_line_simplification_tolerance=None, populate_directions=False, directions_language='en', directions_style_name='NA Desktop', travel_mode='Custom', impedance='Drive Time', gis=None, time_zone_usage_for_time_fields='GEO_LOCAL', save_output_layer=False, overrides=None, save_route_data=False, time_impedance=None, distance_impedance=None, populate_stop_shapes=False, output_format=None, future=False, ignore_invalid_order_locations=False, ignore_network_location_fields=False, locate_settings=None)
```

Useful layer class entry points:

```python
RouteLayer(url, gis=None, **kwargs)
RouteLayer.solve(stops, barriers=None, polyline_barriers=None, polygon_barriers=None, travel_mode=None, ...)
ServiceAreaLayer(url, gis=None, **kwargs)
ClosestFacilityLayer(url, gis=None, **kwargs)
ODCostMatrixLayer(url, gis=None, **kwargs)
NetworkDataset(url, gis=None)
```

Important notes:

- The core solvers expect `FeatureSet` inputs for stops, incidents, facilities, demand points, orders, depots, and barriers.
- `time_of_day` and the related time-zone arguments are often the difference between a good solve and a confusing one.
- If the service is missing, invalid, or unauthorized, validate the inputs and explain the service requirement instead of pretending a local solve exists.

## Geoenrichment signatures

```python
enrich(study_areas, data_collections=None, analysis_variables=None, comparison_levels=None, add_derivative_variables=None, intersecting_geographies=None, return_geometry=True, gis=None, proximity_type=None, proximity_value=None, proximity_metric=None, sanitize_columns=True)
create_report(study_areas, report=None, export_format='pdf', report_fields=None, options=None, return_type=None, use_data=None, in_sr=4326, out_name=None, out_folder=None, gis=None)
standard_geography_query(source_country=None, country_dataset=None, layers=None, ids=None, geoquery=None, return_sub_geography=False, sub_geography_layer=None, sub_geography_query=None, out_sr=4326, return_geometry=False, return_centroids=False, generalization_level=0, use_fuzzy_search=False, feature_limit=1000, as_featureset=False, gis=None)
get_countries(gis=None, as_df=True)
interesting_facts(study_areas, *, study_area_options=None, use_data=None, variables_filter=None, analysis_variables=None, data_collections=None, variable_types=None, comparison_layer='Admin3', spatial_filter=None, thresholds=None, remove_similar_facts=True, result_record_count=10, return_explanation=True, out_statistics=None, out_histogram=None, out_fields=None, return_geometry=False, out_sr=None, gis=None)
service_limits(gis=None)
```

```python
Country(iso3, gis=None, year=None, **kwargs)
Country.enrich(study_areas, enrich_variables=None, return_geometry=True, standard_geography_level=None, standard_geography_id_column=None, proximity_type=None, proximity_value=None, proximity_metric=None, output_spatial_reference=None, **kwargs)
BufferStudyArea(area=None, radii=None, units=None, overlap=True, travel_mode=None)
```

Important notes:

- `study_areas` can be addresses, geometries, points, polygons, or country-specific helper objects depending on the call path.
- `data_collections` and `analysis_variables` are stable IDs, not display labels.
- `create_report` needs the report id and a writeable output location.
- `Country.data_collections`, `Country.reports`, and `Country.subgeographies` are discovery helpers rather than solve helpers.
