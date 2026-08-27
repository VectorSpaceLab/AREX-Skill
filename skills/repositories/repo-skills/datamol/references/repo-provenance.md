# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T19:38:39Z",
  "repository": {
    "name": "datamol",
    "remote_url": "https://github.com/datamol-io/datamol",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "409c5772736350441a676204c6c4cdb89a075225",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "datamol",
      "version": null,
      "import_names": ["datamol"]
    }
  ],
  "evidence": {
    "source_roots": ["datamol/"],
    "docs": ["README.md", "docs/index.md", "docs/usage.md", "docs/api/", "docs/tutorials/"],
    "examples": ["docs/tutorials/", "notebooks/"],
    "tests": ["tests/"],
    "configs": ["pyproject.toml", "mkdocs.yml", "env.yml", "binder/environment.yml"],
    "data": ["datamol/data/", "tests/data/", "docs/tutorials/data/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ materially from the `dirty_paths` list, run `refresh-repo-skill`.
- If package metadata, supported Python/RDKit combinations, public API entry points, docs tutorials, or tests for the covered workflows changed, run `refresh-repo-skill`.
- The package version is recorded as `null` because this checkout uses dynamic versioning and the private inspection install used a temporary local build override that should not be published as a public version baseline.
