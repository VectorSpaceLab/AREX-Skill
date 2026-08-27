# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
`segment-geospatial`. If the current commit, dirty state, package version,
public API surface, or major evidence paths differ from this snapshot, run a
refresh before relying on stale guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:58:03Z",
  "repository": {
    "name": "segment-geospatial",
    "remote_url": "https://github.com/opengeos/segment-geospatial.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5a3185301b57cfe46671e2dd87815b61fb947ae2",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "segment-geospatial",
      "version": "1.4.1",
      "import_names": ["samgeo"]
    }
  ],
  "entry_points": [
    {
      "name": "samgeo-api",
      "target": "samgeo.api:main"
    }
  ],
  "evidence": {
    "source_roots": ["samgeo/"],
    "package_metadata": ["pyproject.toml", "requirements.txt", "requirements_dev.txt", "requirements_docs.txt", "MANIFEST.in"],
    "docs": ["README.md", "docs/installation.md", "docs/usage.md", "docs/api.md", "docs/faq.md", "docs/*.md"],
    "examples": ["docs/examples/*.ipynb", "docs/workshops/*.ipynb"],
    "tests": ["tests/test_api.py", "tests/test_common.py", "tests/test_model_registry.py", "tests/test_samgeo.py", "tests/test_samgeo3.py", "tests/test_utmconv.py"],
    "scripts": ["scripts/convert_notebooks.py", "scripts/upload_to_qgis_plugin_repo.py", "package_plugin.py"],
    "excluded_runtime_scopes": ["qgis-samgeo-plugin/", "agent-harness/", "paper/", "samgeo/fer.py GDAL path", "detectree2 external runtime path"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale.
- If package version, optional extras, CLI entry points, or model registry
  constants changed, refresh even when the commit is close.
- If `samgeo/samgeo3.py`, `samgeo/api.py`, `samgeo/common.py`, optional model
  modules, or test-backed API behavior changed, refresh the relevant sub-skill.
- If a checkout adds first-class QGIS, detectree2, FER/GDAL, or maintainer CLI
  requirements and the user wants those workflows, extend or refresh this skill
  before using the old gap notes.
