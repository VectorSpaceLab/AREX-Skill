---
name: annotation-visualization
description: "Plan and implement TIAToolbox annotation stores, DSL filters,
  graph overlays, and visualization/tile-server data layouts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TIAToolbox Annotation Visualization

Use this sub-skill when a task involves TIAToolbox annotations, annotation stores, GeoJSON or HoVerNet-style overlays, graph overlays, DSL filters, or visualization command planning.

## Route here for

- Creating or inspecting `Annotation` objects and `SQLiteStore` or `DictionaryStore` containers.
- Querying annotations by spatial bounds, Shapely geometry, properties, or DSL `where` filters.
- Converting overlay data among `AnnotationStore`, GeoJSON-like feature collections, HoVerNet-style `.dat` records, and graph JSON layouts.
- Planning visualization with `tiatoolbox visualize`, `tiatoolbox show-wsi`, or `TileServer` without launching servers unless the user explicitly asks.
- Diagnosing overlay visibility, coloring, property, filter, and remote/port issues.

## Route elsewhere

- Route model-output generation and inference configuration to `../model-inference/SKILL.md`.
- Route WSI loading, slide metadata, resolution, and registration image metadata to `../wsi-io/SKILL.md`.
- Route exact CLI option tables and global configuration conventions to `../cli-and-configuration/SKILL.md`.

## Reference map

- API and query patterns: `references/api-reference.md`
- Overlay and data layout formats: `references/data-formats.md`
- End-to-end planning workflows: `references/workflows.md`
- Failure diagnosis: `references/troubleshooting.md`
- Safe local smoke check: `scripts/annotation_store_smoke.py`

## Safe default approach

1. Identify whether the user needs an in-memory check, a persistent `.db`, a GeoJSON/dat conversion, a graph overlay, or an interactive viewer plan.
2. Normalize properties early: prefer stable keys such as `type`, `score`, `color`, class labels, and model-specific fields.
3. Use `SQLiteStore` for large or persistent overlays; use `DictionaryStore` for tiny examples and quick in-memory manipulation.
4. Validate geometry, basename matching, property ranges, and DSL filters before launching a browser or server.
5. If visualization is needed, prepare commands with `--noshow` for headless checks or document SSH port forwarding for remote runs.

## Minimal smoke check

Run this only as a local sanity check; it does not launch `TileServer`, Bokeh, or a browser:

```bash
python scripts/annotation_store_smoke.py
```
