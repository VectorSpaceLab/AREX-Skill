# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a LEANN checkout.
If the current commit, source dirty state, package metadata, public entry points,
or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:53:07Z",
  "repository": {
    "name": "LEANN",
    "remote_url": "https://github.com/StarTrail-org/LEANN.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "dc85934f318c9c7f981cbe9b66042d00ec2cb634",
    "working_tree": "clean before generated skill outputs",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "leann",
      "version": "0.3.8",
      "import_names": ["leann"]
    },
    {
      "name": "leann-core",
      "version": "0.3.8",
      "import_names": ["leann"]
    },
    {
      "name": "leann-backend-hnsw",
      "version": "0.3.8",
      "import_names": ["leann_backend_hnsw"]
    },
    {
      "name": "leann-backend-diskann",
      "version": "0.3.8",
      "import_names": ["leann_backend_diskann"]
    },
    {
      "name": "leann-backend-ivf",
      "version": "0.3.6",
      "import_names": ["leann_backend_ivf"]
    },
    {
      "name": "leann-backend-flashlib",
      "version": "0.3.6",
      "import_names": ["leann_backend_flashlib"]
    },
    {
      "name": "leann-backend-flashlib-ivf",
      "version": "0.3.6",
      "import_names": ["leann_backend_flashlib_ivf"]
    }
  ],
  "evidence": {
    "source_roots": [
      "packages/leann-core/src/leann",
      "packages/leann-backend-hnsw",
      "packages/leann-backend-ivf",
      "packages/leann-backend-diskann",
      "packages/leann-backend-flashlib",
      "packages/leann-backend-flashlib-ivf",
      "packages/leann-mcp"
    ],
    "docs": ["README.md", "llms.txt", "docs", "packages/leann-mcp/README.md"],
    "examples": ["apps", "examples"],
    "tests": ["tests"],
    "configs": [
      "pyproject.toml",
      "packages/leann/pyproject.toml",
      "packages/leann-core/pyproject.toml",
      ".github/workflows"
    ],
    "contributor_rules": ["CLAUDE.md", "docs/CONTRIBUTING.md"]
  }
}
```

The working tree was checked before generated skill and review artifacts were
written. Initializing the bounded HNSW submodules at their recorded commits did
not change tracked superproject content. Generated files under `skills/` are not
source-evidence dirtiness.

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If tracked source files are dirty when this snapshot was source-clean, or the
  initialized submodule commits differ, refresh before relying on native-build
  details.
- Refresh when package versions, backend registry names, CLI commands, API
  signatures, index artifact schemas, provider types, or service tool schemas
  change even if the high-level project name is unchanged.
- Component versions intentionally differ in this snapshot: core/HNSW/DiskANN
  are `0.3.8`, while IVF and both FlashLib packages declare `0.3.6`. Do not
  normalize those values from memory.
