# Repository Provenance

## Purpose

Read this before deciding whether the GeoSeg operating graph matches a current
checkout. If the source commit, dirty source paths, public entry points, or
major evidence paths differ, run `refresh-repo-skill` rather than assuming the
graph is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T18:40:00Z",
  "repository": {
    "name": "GeoSeg",
    "remote_url": "https://github.com/WangLibo1995/GeoSeg.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9453fe48209c4626b29e35e61bab93b61212c4b1",
    "working_tree": "dirty at source capture",
    "dirty_paths": ["skills/GeoSeg.log"]
  },
  "packages": [
    {
      "name": "GeoSeg source checkout",
      "version": null,
      "import_names": ["geoseg", "tools"]
    }
  ],
  "evidence": {
    "source_roots": ["geoseg", "tools"],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": ["config"]
  }
}
```

## Interpretation

- The checkout had no packaging metadata (`pyproject.toml`, `setup.py`, or
  `setup.cfg`), so this graph describes source modules and the documented
  command-line entry points rather than a released distribution version.
- The source snapshot was taken before the generated runtime tree and review
  artifacts were written. Those generated outputs are not repository evidence
  or a reason to refresh the graph.
- The source tree had no datasets, pretrained weights, checkpoints, native
  tests, notebooks, or examples. The graph records those as explicit external
  prerequisites.
- `requirements.txt` names both `lightning==2.0.0` and
  `pytorch-lightning==2.3.0`; source imports `pytorch_lightning`. The inspection
  environment verified the source-used package and treated the redundant
  meta-package's pydantic conflict as a setup warning.

## Refresh check

- Compare `git rev-parse HEAD` with the commit above.
- Compare source-side dirty paths and public entry points, ignoring the managed
  generated tree and review artifacts.
- Reinspect when `geoseg/`, `tools/`, `config/`, `README.md`,
  `requirements.txt`, or any root entry-point script changes.
- Revalidate dataset class tuples, constructor signatures, config behavior,
  optional dependencies, and CUDA assumptions after a meaningful source change.
