# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of GeoAI. If the current repo commit, dirty state, package version, or public evidence paths differ materially from this snapshot, refresh the repo skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T16:37:04Z",
  "repository": {
    "name": "geoai",
    "remote_url": "https://github.com/opengeos/geoai.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "44c4ecf9a35c4af337f6d4331fdab377c5e307d6",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "geoai-py",
      "version": "0.42.0",
      "import_names": ["geoai"]
    }
  ],
  "evidence": {
    "source_roots": ["geoai"],
    "docs": ["README.md", "docs"],
    "examples": ["docs/examples", "docs/examples/pipelines"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "requirements.txt", "pytest.ini"],
    "integrations": ["qgis_plugin", "geoai-mcp-server"],
    "source_scripts": ["scripts"]
  }
}
```

## Refresh check

Refresh this skill when:

- `git rev-parse HEAD` differs from the commit above.
- Public package metadata, console entry points, optional extras, or major module exports change.
- The QGIS plugin or MCP server layouts change.
- New public workflows appear in docs, examples, tests, or scripts.
- The current checkout is clean but this snapshot was dirty, or the dirty paths differ and may affect package evidence.

## Notes

This skill was generated from a checkout whose only known dirty source area was the repository-local `skills/` production output area. Runtime skill files do not depend on the original checkout remaining available.
