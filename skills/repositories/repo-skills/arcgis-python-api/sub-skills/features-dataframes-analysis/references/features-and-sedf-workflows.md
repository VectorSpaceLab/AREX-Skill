# Features and SEDF Workflows

This reference turns the feature-layer, geometry, SEDF, append, replica, and hosted-analysis evidence into a working playbook.

## 1. Decide local or hosted execution first

| Need | Start with | Notes |
| --- | --- | --- |
| inspect or transform rows already in memory | `Geometry` or SEDF methods | No GIS service is needed.
| query a hosted feature layer without mutating it | `FeatureLayer.query(...)` | Use `as_df=True` or `query().sdf` when you want a DataFrame.
| edit, append, or delete hosted features | `edit_features(...)` or `append(...)` | Requires a service-backed layer and the right capabilities.
| run an analysis that returns a hosted layer | `analysis`, `manage_data`, `use_proximity`, `find_locations`, or `summarize_data` | These are service-backed operations.
| geocode addresses | route away | `GeoAccessor.from_df` and locator-driven workflows belong to the location-services path.

If the request only has pandas rows, prefer local geometry and SEDF operations. If it needs a hosted result layer, a GIS connection, or service credits, treat it as a hosted workflow.

## 2. Query and schema preflight

Always inspect the source schema before editing or appending.

Checklist:

- confirm the geometry type you expect
- confirm the spatial reference on both sides
- confirm the object-ID field and, if needed, the global-ID field
- confirm field names, types, lengths, and nullability
- confirm the layer capability you need, such as editing or sync
- preflight with counts or IDs before downloading all records

Typical read patterns:

```python
layer.query(where="1=1", out_fields="*", return_count_only=True)
layer.query(where="1=1", out_fields="*", return_ids_only=True)
layer.query(where="POP2010 > 1000000", out_fields=["NAME", "POP2010"], as_df=True)
```

For spatial reads, build a geometry filter with the geometry filter helpers and keep the spatial reference aligned with the layer or output `out_sr`.

## 3. Editing and append workflow

Use `query()` to find the target rows first, then build edits with explicit attributes and geometry.

Common edit payload rules:

- updates and deletes need the correct object IDs or global IDs
- adds need the required fields and a valid geometry when the layer is spatial
- the edit response should be checked row by row, not just as a whole
- if the service supports global IDs and you are using them, set `use_global_ids=True`
- if the layer is versioned, pass `gdb_version` to target the right branch version

Minimal structure:

```python
edit = {
    "attributes": {"OBJECTID": 1, "name": "updated"},
    "geometry": {"x": -118.15, "y": 33.80, "spatialReference": {"wkid": 4326}},
}
result = layer.edit_features(updates=[edit])
```

Bulk append is a different path:

- use `FeatureLayer.append(...)`
- choose the right `upload_format`
- map fields explicitly when source and target names differ
- use `upsert`, `upsert_matching_field`, `update_geometry`, `skip_updates`, and `skip_inserts` deliberately
- re-query after the append to verify the row count and a few sample records

## 4. Replicas and branch versioning

### Branch versioning

A feature layer collection exposes `versions` only when the service has versioned data.

Use the version manager when you need:

- list/search versions
- create a new version
- open a version for read or edit mode
- purge a lock or delete a version after the work is complete

Typical flow:

1. check that versioned data exists
2. create or select the version
3. use `gdb_version` when querying or editing the layer
4. reconcile/post/delete only when the workflow requires it

### Sync and replicas

A sync-enabled feature layer collection exposes `replicas`.

Use it when you need:

- a disconnected replica for local editing
- replica inspection or cleanup
- layer-specific query filters or geometry filters in the replica definition

Replica creation usually needs:

- layer ids
- optional per-layer queries
- optional geometry filters
- a target type and data format

If the service is not sync-enabled or branch-versioned, do not promise replica or version workflows.

## 5. SEDF IO and the spatial namespace

The spatially enabled dataframe is the local workhorse for vector data.

Common entry points:

- `from_layer(...)` for hosted feature layers
- `from_featureclass(...)` for local shapefiles, file geodatabases, mobile geodatabases, or SQLite sources
- `from_xy(...)` for coordinate columns
- `from_table(...)`, `from_geodataframe(...)`, and `from_feather(...)` when the input format already fits those workflows
- `from_df(...)` for address geocoding, which is a location-service workflow and should be routed away when the question is really about locators or credits

Common exit points:

- `to_featureclass(...)` for local vector files and databases
- `to_featurelayer(...)` for publishing to a hosted feature layer
- `to_featureset()` for JSON-style round-tripping
- `to_featurecollection()` when a feature collection is the right wrapper
- `to_parquet(...)` when a Parquet export is useful for downstream pandas work

Useful spatial namespace checks:

- `geometry_type`
- `sr`
- `full_extent`
- `bbox`
- `validate(strict=False)`
- `join(...)`
- `overlay(...)`
- `sindex(...)`

Geometry-engine notes from the guide set:

- ArcPy is the richest engine when it is available
- otherwise, shapely, Fiona, and PyShp support some local file workflows
- if the required local engine is missing, keep the workflow in memory or ask for the needed dependency

## 6. Geometry objects and spatial filters

Create geometry objects locally with `Point`, `Polyline`, `Polygon`, or the generic `Geometry` wrapper.

Before any spatial join or overlay, verify:

- the geometry is valid
- both sides use compatible spatial references
- the output needs are clear: local-only, projected output, or hosted analysis

Useful local operations:

- `buffer`
- `intersect`
- `union`
- `difference`
- `symmetric_difference`
- `generalize`
- `contains`
- `within`
- `overlaps`
- `touches`
- `crosses`
- `distance_to`
- `is_valid`

Spatial filter helpers:

- `intersects`
- `contains`
- `overlaps`
- `crosses`
- `touches`
- `within`
- `envelope_intersects`
- `index_intersects`

Use geometry filters for hosted layer queries, and use local geometry methods or SEDF spatial operations when the data already lives in memory.

## 7. Hosted analysis families

### Overlay and data management

- `analysis.overlay_layers(...)`
- `analysis.join_features(...)`
- `analysis.merge_layers(...)`
- `manage_data.overlay_layers(...)`
- `manage_data.dissolve_boundaries(...)`
- `manage_data.extract_data(...)`
- `manage_data.merge_layers(...)`
- `manage_data.generate_tessellation(...)`
- `manage_data.create_route_layers(...)`

### Proximity and routing

- `use_proximity.create_buffers(...)`
- `use_proximity.find_nearest(...)`
- `use_proximity.connect_origins_to_destinations(...)`
- `use_proximity.create_drive_time_areas(...)`
- `use_proximity.plan_routes(...)`

### Location discovery and environmental analysis

- `find_locations.derive_new_locations(...)`
- `find_locations.find_existing_locations(...)`
- `find_locations.find_similar_locations(...)`
- `find_locations.choose_best_facilities(...)`
- `find_locations.create_viewshed(...)`
- `find_locations.create_watersheds(...)`
- `find_locations.trace_downstream(...)`
- `find_locations.find_centroids(...)`

### Summaries

- `summarize_data.aggregate_points(...)`
- `summarize_data.join_features(...)`
- `summarize_data.summarize_within(...)`
- `summarize_data.summarize_nearby(...)`
- `summarize_data.summarize_center_and_dispersion(...)`

These functions are service-backed. Expect asynchronous jobs, output items or layers, and possible credit consumption.

## 8. What to return to the caller

When the result is a hosted layer or item:

- inspect the item or layer URL
- query the first layer for a small sample
- return a short note about capability and any service requirement

When the result is a FeatureSet:

- inspect `features`, `fields`, `geometry_type`, `spatial_reference`, `object_id_field_name`, and `global_id_field_name`
- convert to SEDF if the caller wants dataframe operations

When the result is local SEDF:

- inspect `shape`, `columns`, `spatial.geometry_type`, `spatial.sr`, and `spatial.validate(strict=False)`
- use local joins/overlays/geometry methods before escalating to a hosted analysis
