# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of GeoPandas. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T16:34:09Z",
  "repository": {
    "name": "geopandas",
    "remote_url": "https://github.com/geopandas/geopandas.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "57c0531b7805e7ca8873b04400adcb88e37a314b",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "geopandas",
      "version": "0.1.dev1+g57c0531b7",
      "import_names": ["geopandas"]
    }
  ],
  "evidence": {
    "source_roots": ["geopandas/", "geopandas/io/", "geopandas/tools/"],
    "docs": ["README.md", "doc/source/getting_started.md", "doc/source/getting_started/install.rst", "doc/source/docs/user_guide/", "doc/source/docs/reference/", "doc/source/gallery/"],
    "examples": ["examples/README.md", "doc/source/gallery/*.ipynb", "doc/source/docs/user_guide/*.ipynb"],
    "tests": ["geopandas/tests/", "geopandas/tools/tests/", "geopandas/io/tests/"],
    "configs": ["pyproject.toml", "environment.yml", "environment-dev.yml", "ci/envs/*.yaml"],
    "source_scripts": ["ci/scripts/setup_postgres.sh", "geopandas/io/tests/generate_legacy_storage_files.py", "doc/source/_static/code/buffer.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ materially from `skills/`, run `refresh-repo-skill`.
- If package metadata, public entry points, dependency requirements, optional dependency groups, or major method signatures changed even on the same commit, run `refresh-repo-skill`.
- If GeoPandas changes its base I/O engine, Python support floor, CRS semantics, or optional visualization/geocoding dependencies, refresh before relying on this skill for those workflows.
