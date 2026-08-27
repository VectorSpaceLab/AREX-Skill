---
name: features-dataframes-analysis
description: "Work with feature layers, FeatureSet/Feature, spatially enabled
  dataframes, geometry operations, replicas, branch versioning, and hosted
  feature analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Features, DataFrames, and Analysis

Use this sub-skill when the task is about:

- feature layers, tables, `Feature`, `FeatureSet`, and `FeatureLayerCollection`
- spatially enabled dataframes (SEDF), spatial joins/overlays, plotting, and local vector IO
- `Geometry` creation, validation, projection, and spatial predicates
- edits, appends, attachments, replicas, and branch versioning
- hosted feature and spatial analysis functions in `analysis`, `manage_data`, `use_proximity`, `find_locations`, and `summarize_data`

Start here:

- [features and SEDF workflows](references/features-and-sedf-workflows.md)
- [geometry and analysis API](references/geometry-and-analysis-api.md)
- [troubleshooting](references/troubleshooting.md)
- [local geometry smoke](scripts/local_geometry_smoke.py)

Operating rules:

1. Separate local geometry/SEDF work from hosted service calls.
2. Before editing, appending, versioning, or analyzing a layer, validate field names and types, object ID/global ID availability, geometry type, spatial reference, and service capabilities.
3. Use `query(return_count_only=True)` and `query(return_ids_only=True)` as preflight checks before pulling large result sets.
4. Use `FeatureLayer.append` for bulk loads; do not assume a public `manage_data.append_data` helper exists.
5. For local data, prefer `GeoAccessor.from_layer`, `from_featureclass`, `from_xy`, `to_featureclass`, `to_featureset`, and `to_featurelayer` when the task stays on disk or in memory.
6. For hosted analysis functions, expect service-backed outputs, async jobs, and possible credit usage.
7. For sync-enabled or branch-versioned services, confirm `syncEnabled` or `hasVersionedData` before using replicas or versions.
8. Use the smoke script before writing a service-dependent workflow.

Route elsewhere when the request is about:

- imagery or raster analytics -> imagery-raster-analysis
- geocoding, routing/network, geoenrichment, or map widgets -> mapping-location-services
- `arcgis.learn` or model training/inference -> deep-learning
