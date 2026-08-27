# Geometry and Analysis API

This reference records the verified surface used by the sub-skill drafting pass. Treat it as the baseline for later refreshes.

## Verified package snapshot

- `arcgis` 2.4.1.3
- `arcgis-mapping` 4.31.0
- `pandas` 2.2.3
- `numpy` 1.26.4

## Module exports

### `arcgis.features.analysis`

```text
aggregate_points
calculate_composite_index
calculate_density
choose_best_facilities
connect_origins_to_destinations
create_buffers
create_drive_time_areas
create_route_layers
create_viewshed
create_watersheds
derive_new_locations
dissolve_boundaries
enrich_layer
extract_data
find_centroids
find_existing_locations
find_hot_spots
find_nearest
find_outliers
find_point_clusters
find_similar_locations
generate_tessellation
interpolate_points
join_features
merge_layers
overlay_layers
plan_routes
summarize_center_and_dispersion
summarize_nearby
summarize_within
trace_downstream
```

### `arcgis.features.manage_data`

```text
Any
FeatureCollection
FeatureLayer
FeatureLayerCollection
GIS
Item
Optional
Union
annotations
create_route_layers
dissolve_boundaries
extract_data
generate_tessellation
inspect_function_inputs
merge_layers
overlay_layers
```

### `arcgis.features.use_proximity`

```text
Any
FeatureCollection
FeatureLayer
FeatureLayerCollection
GIS
Item
Optional
U
Union
annotations
connect_origins_to_destinations
create_buffers
create_drive_time_areas
datetime
find_nearest
inspect_function_inputs
logging
network
plan_routes
```

### `arcgis.features.find_locations`

```text
Any
FeatureCollection
FeatureLayer
FeatureLayerCollection
GIS
Item
Optional
U
Union
annotations
choose_best_facilities
create_viewshed
create_watersheds
datetime
derive_new_locations
find_centroids
find_existing_locations
find_similar_locations
inspect_function_inputs
logging
network
trace_downstream
```

### `arcgis.features.summarize_data`

```text
Any
FeatureCollection
FeatureLayer
FeatureLayerCollection
GIS
Item
Optional
U
Union
aggregate_points
annotations
datetime
inspect_function_inputs
join_features
network
summarize_center_and_dispersion
summarize_nearby
summarize_within
```

### `arcgis.geometry`

Relevant exports for this sub-skill include:

```text
Geometry
Point
Polyline
Polygon
SpatialReference
filters
functions
project
buffer
intersect
union
difference
symmetric_difference
generalize
relation
lengths
areas_and_lengths
offset
simplify
```

### `arcgis.geometry.filters`

```text
intersects
contains
overlaps
crosses
touches
within
envelope_intersects
index_intersects
```

## Core signatures

### Feature layer and feature objects

- `FeatureLayer(url, gis=None, container=None, dynamic_layer=None)`
- `FeatureLayer.query(where='1=1', out_fields='*', time_filter=None, geometry_filter=None, return_geometry=True, return_count_only=False, return_ids_only=False, return_distinct_values=False, return_extent_only=False, group_by_fields_for_statistics=None, statistic_filter=None, result_offset=None, result_record_count=None, object_ids=None, distance=None, units=None, max_allowable_offset=None, out_sr=None, geometry_precision=None, gdb_version=None, order_by_fields=None, out_statistics=None, return_z=False, return_m=False, multipatch_option=None, quantization_parameters=None, return_centroid=False, return_all_records=True, result_type=None, historic_moment=None, sql_format=None, return_true_curves=False, return_exceeded_limit_features=None, as_df=False, datum_transformation=None, time_reference_unknown_client=None, **kwargs)`
- `FeatureLayer.edit_features(adds=None, updates=None, deletes=None, gdb_version=None, use_global_ids=False, rollback_on_failure=True, return_edit_moment=False, attachments=None, true_curve_client=False, session_id=None, use_previous_moment=False, datum_transformation=None, future=False)`
- `FeatureLayer.append(item_id=None, upload_format='featureCollection', source_table_name=None, field_mappings=None, edits=None, source_info=None, upsert=False, skip_updates=False, use_globalids=False, update_geometry=True, append_fields=None, rollback=False, skip_inserts=None, upsert_matching_field=None, upload_id=None, layer_mappings=None, *, return_messages=None, future=False, gdb_version=None)`
- `FeatureLayer.delete_features(deletes=None, where=None, geometry_filter=None, gdb_version=None, rollback_on_failure=True, return_delete_results=True, future=False)`
- `FeatureSet(features, fields=None, has_z=False, has_m=False, geometry_type=None, spatial_reference=None, display_field_name=None, object_id_field_name=None, global_id_field_name=None)`
- `FeatureSet.from_dict(featureset_dict)`
- `FeatureSet.from_json(json_str)`
- `FeatureSet.from_geojson(geojson)`
- useful properties: `geometry_type`, `spatial_reference`, `object_id_field_name`, `global_id_field_name`, `fields`, `features`

### GeoAccessor / SEDF

`GeoAccessor` is accessed as `df.spatial` on a pandas DataFrame.

- `from_xy(df, x_column, y_column, sr=4326, z_column=None, m_column=None, **kwargs)`
- `from_layer(layer)`
- `from_featureclass(location, **kwargs)`
- `to_featureclass(location, overwrite=True, has_z=None, has_m=None, sanitize_columns=True)`
- `to_featurelayer(title=None, gis=None, tags=None, folder=None, sanitize_columns=False, service_name=None, **kwargs)`
- `to_featureset()`
- `validate(strict=False)`
- `join(right_df, how='inner', op='intersects', left_tag='left', right_tag='right')`
- `overlay(sdf, op='union')`
- `sindex(stype='quadtree', reset=False, **kwargs)`
- properties: `geometry_type`, `sr`, `full_extent`, `bbox`

### Geometry

- `Geometry(iterable=None, **kwargs)`
- `buffer(distance)`
- `contains(second_geometry, relation=None)`
- `crosses(second_geometry)`
- `difference(second_geometry)`
- `disjoint(second_geometry)`
- `distance_to(second_geometry)`
- `equals(second_geometry)`
- `generalize(max_offset)`
- `intersect(second_geometry, dimension=1)`
- `is_valid()`
- `overlaps(second_geometry)`
- `symmetric_difference(second_geometry)`
- `touches(second_geometry)`
- `union(second_geometry)`
- `within(second_geometry, relation=None)`

## Replica and versioning entry points

- `FeatureLayerCollection(url, gis=None)`
- `FeatureLayerCollection.versions` returns a `VersionManager` when the service has versioned data
- `VersionManager.all`
- `VersionManager.search(owner=None, show_hidden=False)`
- `VersionManager.get(version, mode=None)`
- `VersionManager.create(name, permission='public', description='')`
- `VersionManager.purge(version, owner=None)`
- `FeatureLayerCollection.replicas` is exposed on sync-enabled collections through `SyncManager`
- `SyncManager.get_list()`
- `SyncManager.create(replica_name, layers, layer_queries=None, geometry_filter=None, replica_sr=None, transport_type='esriTransportTypeUrl', return_attachments=False, return_attachments_databy_url=False, asynchronous=False, attachments_sync_direction='none', sync_model='none', data_format='json', replica_options=None, wait=False, out_path=None, sync_direction=None, target_type='client', transformations=None, time_reference_unknown_client=None)`
- `SyncManager.get(replica_id)`
- `SyncManager.unregister(replica_id)`

## Inspection gap to keep in mind

The inspected surface did not expose a public `arcgis.features.manage_data.append_data` export. Treat append workflows as `FeatureLayer.append` unless a later refresh proves otherwise.
