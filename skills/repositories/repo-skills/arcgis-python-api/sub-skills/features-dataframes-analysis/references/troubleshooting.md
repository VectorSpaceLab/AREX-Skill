# Troubleshooting

This reference covers the failures most likely to appear in feature-layer, geometry, SEDF, append, versioning, replica, and hosted-analysis workflows.

## 1. Schema or field mismatch

Symptoms:

- append or edit fails with a field error
- a column disappears after a dataframe transformation
- `FeatureSet` or SEDF output has unexpected names or types

Safe checks:

- compare dataframe columns with the service field metadata
- verify field types, lengths, nullability, and domain expectations
- make sure geometry columns are not accidentally renamed away
- confirm the object-ID and global-ID field names before calling edit or append

Likely fixes:

- rename or drop extra columns before publishing or appending
- coerce number/date columns to the target type
- rebuild the `FeatureSet` dictionary with explicit field definitions when a round-trip matters
- sanitize columns only when the target service accepts the transformed names

## 2. Object ID or global ID problems

Symptoms:

- update/delete affects the wrong record or nothing at all
- append or sync reports partial success
- `FeatureSet` looks valid but the service rejects the edit payload

Safe checks:

- preflight with `query(return_count_only=True)` and `query(return_ids_only=True)`
- confirm the target layer's object-ID field and, if needed, global-ID field
- check whether `use_global_ids=True` is appropriate for the service
- do not rely on display names as record keys

Likely fixes:

- supply the exact object ID or global ID in the edit payload
- target the correct branch version with `gdb_version` when the service is versioned
- re-query after the change to confirm the record moved as expected

## 3. Geometry or CRS mismatch

Symptoms:

- a spatial join returns zero rows
- a filter or overlay misses obvious features
- geometry operations produce invalid or empty results

Safe checks:

- call `geometry.is_valid()` on local geometries
- inspect `df.spatial.geometry_type` and `df.spatial.sr`
- compare the spatial reference on both sides before joining or overlaying
- make sure the output spatial reference is explicit when the task needs it

Likely fixes:

- project before combining datasets instead of editing coordinates by hand
- use `out_sr` or a geometry projection step when the output needs a different CRS
- rebuild bad geometries if the source rings or paths are invalid

## 4. Edit or append result ambiguity

Symptoms:

- the service returns a mixed success/failure response
- only some rows were changed
- the error does not point to a single column or row

Safe checks:

- inspect each entry in `addResults`, `updateResults`, and `deleteResults`
- look for `success`, `objectId`, `globalId`, and `error` per row
- confirm the payload includes the geometry where needed
- verify the service supports the operation before retrying

Likely fixes:

- correct the failed rows only, then retry
- split a large append into smaller chunks when diagnosing schema issues
- use `rollback_on_failure=True` when an all-or-nothing behavior is preferred

## 5. Hosted analysis requires a service

Symptoms:

- a user asks for `overlay_layers`, `summarize_within`, `create_buffers`, or a similar hosted tool, but only local rows exist
- the workflow has no GIS connection or portal permissions
- the service expects credits or a named analysis service

Safe checks:

- confirm whether the data is only local or actually published
- confirm that the intended GIS/service is available
- identify whether the request is really a local dataframe problem instead

Likely fixes:

- use local `Geometry` or SEDF operations when the data already lives on disk or in memory
- ask for a hosted layer and the right credentials when a service-backed result is required
- do not promise a hosted analysis when the environment cannot supply it

## 6. Replicas or branch versions are unavailable

Symptoms:

- `versions` is missing or empty
- `replicas` is missing or empty
- replica creation or branch editing returns a capability error

Safe checks:

- confirm `FeatureLayerCollection.properties.hasVersionedData`
- confirm `FeatureLayerCollection.properties.syncEnabled`
- check whether the service is hosted, versioned, or sync-enabled in the first place

Likely fixes:

- switch to a non-versioned local workflow if the service is not configured for replicas or versions
- do not fabricate version names or replica IDs
- keep the workflow read-only unless the service explicitly supports editing

## 7. Local file IO engine limitations

Symptoms:

- `from_featureclass` or `to_featureclass` fails on a local file
- shapefile or geodatabase access behaves differently on different machines
- the guide path expects a local engine that is not installed here

Safe checks:

- identify the local geometry engine available in the environment
- distinguish ArcPy-backed workflows from shapely/Fiona/PyShp-backed workflows
- keep the task in memory when the local engine is missing

Likely fixes:

- use ArcPy when it is available and the task needs full local file support
- otherwise fall back to the supported open-source engine path for that file type
- prefer CSV/DataFrame or in-memory geometry when file IO is not the point of the task

## 8. Notebook plotting does not render

Symptoms:

- `df.spatial.plot(...)` returns but nothing is visible
- map widgets do not render in the notebook

Safe checks:

- confirm the notebook front end is available
- confirm `arcgis-mapping` is installed
- do not confuse visualization failure with analysis failure

Likely fixes:

- treat plotting as optional presentation, not as the proof that the workflow succeeded
- use dataframe and geometry checks when a visual widget is unavailable

## 9. Good fallback when only local data exists

If the user asks for a hosted spatial analysis but only provides local pandas rows:

1. convert the rows to SEDF with `from_xy(...)` or another local reader
2. use `Geometry` methods or SEDF `join` / `overlay`
3. return a note that hosted analysis would need a published layer and a GIS service

This keeps the response useful without inventing a service-backed result.
