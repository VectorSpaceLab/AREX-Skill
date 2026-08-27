# Repository Provenance

Read this before deciding whether the GeoNode operating graph is current for a
checkout. If the commit, package version, public entry points, or major evidence
paths differ, use a refresh workflow before relying on the graph.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "GeoNode",
    "remote_url": "https://github.com/GeoNode/geonode",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "69fe81da9d4959e55a7fb5ab1284792ad514a1b9",
    "working_tree": "clean at source snapshot; generated skill and review outputs were added under skills/ after capture",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "GeoNode",
      "version": "5.1.0.dev0",
      "import_names": ["geonode"]
    }
  ],
  "evidence": {
    "source_roots": ["geonode", "geonode/settings.py", "geonode/urls.py"],
    "docs": ["README.md", "docs/src", "docs/mkdocs.yml"],
    "examples": ["docs/src/development", "docs/src/setup", "create-envfile.py"],
    "tests": ["geonode/**/tests", "geonode/**/test*.py"],
    "configs": ["pyproject.toml", "setup.py", ".env.sample", ".env_dev", ".env_test", "docker-compose.yml", "Dockerfile"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the graph as
  potentially stale.
- If source files under `geonode/`, package metadata, documented API routes,
  service topology, or management command names change, refresh the affected
  sub-skill even if the commit comparison is unavailable.
- The `skills/` output directory is construction output, not source evidence;
  do not use its generated files as proof that the repository itself is clean.
