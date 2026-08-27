# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches a checkout of DataDesigner. If the current repository commit, dirty state, package version, or evidence paths differ materially from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:51:00Z",
  "repository": {
    "name": "DataDesigner",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": "v0.9.1",
    "commit": "27acf141170eceb1e8242c132d56b49107462fce",
    "working_tree": "dirty",
    "dirty_paths": ["skills/DataDesigner.log"]
  },
  "packages": [
    {
      "name": "data-designer",
      "version": "0.9.1",
      "import_names": ["data_designer"]
    },
    {
      "name": "data-designer-config",
      "version": "0.9.1",
      "import_names": ["data_designer.config"]
    },
    {
      "name": "data-designer-engine",
      "version": "0.9.1",
      "import_names": ["data_designer.engine"]
    }
  ],
  "evidence": {
    "source_roots": [
      "packages/data-designer-config/src/data_designer/config",
      "packages/data-designer-engine/src/data_designer/engine",
      "packages/data-designer/src/data_designer"
    ],
    "docs": [
      "README.md",
      "architecture",
      "docs/notebook_source",
      "docs/assets/recipes",
      "fern/assets/recipes"
    ],
    "examples": [
      "docs/notebook_source",
      "docs/assets/recipes",
      "fern/assets/recipes"
    ],
    "tests": [
      "packages/data-designer-config/tests",
      "packages/data-designer-engine/tests",
      "packages/data-designer/tests"
    ],
    "configs": [
      "pyproject.toml",
      "packages/data-designer-config/pyproject.toml",
      "packages/data-designer-engine/pyproject.toml",
      "packages/data-designer/pyproject.toml"
    ]
  }
}
```

## Refresh check

- If the repository commit changes, treat this skill as potentially stale.
- If the public package version changes, re-check the installed package facts.
- If the source roots or CLI entry points move, refresh the skill.

## Notes

- The snapshot was taken from a dirty checkout that already contained a repository-local log file before this skill was generated.
- Generated runtime skill content is intentionally not treated as a source root.
