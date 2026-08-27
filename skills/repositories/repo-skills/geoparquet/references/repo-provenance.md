# Repository Provenance

Read this before deciding whether this operating graph is current for a
GeoParquet checkout. If the source commit, dirty state, package/spec version,
or major evidence paths differ, use `refresh-repo-skill` rather than silently
assuming the graph is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T19:56:10Z",
  "repository": {
    "name": "geoparquet",
    "remote_url": "https://github.com/opengeospatial/geoparquet.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "21eba451ef4a334aed424bc9ad5695fe31fd4e8f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "geoparquet-scripts",
      "version": "0.1.0",
      "import_names": []
    }
  ],
  "specifications": [
    {
      "name": "GeoParquet vector metadata",
      "version": "2.0.0",
      "schema": "format-specs/schema.json"
    },
    {
      "name": "Parquet Raster",
      "version": "alpha / work in progress",
      "schema": "format-specs/parquet-raster.md"
    }
  ],
  "evidence": {
    "source_roots": [],
    "docs": [
      "README.md",
      "format-specs/geoparquet.md",
      "format-specs/compatible-parquet.md",
      "format-specs/distributing-geoparquet.md",
      "format-specs/distributing-geoparquet-tools.md",
      "format-specs/parquet-raster.md"
    ],
    "examples": ["examples", "test_data"],
    "tests": [
      "scripts/test_json_schema.py",
      "scripts/test_example.py"
    ],
    "configs": ["scripts/pyproject.toml", "scripts/uv.lock"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the graph as
  potentially stale and refresh it.
- If `skills/` is clean or its changed paths differ materially from this
  snapshot, refresh the generated graph and its artifacts.
- If the vector schema version, native Parquet requirements, distribution
  recommendations, raster proposal, or contributor helper dependencies change,
  refresh the affected sub-skill and rerun verification.
