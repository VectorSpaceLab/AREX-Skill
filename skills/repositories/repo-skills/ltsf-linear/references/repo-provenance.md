# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the commit, dirty state, package surface, or major evidence paths
differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T21:56:03Z",
  "repository": {
    "name": "LTSF-Linear",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "0c113668a3b88c4c4ee586b8c5ec3e539c4de5a6",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "torch",
      "version": "1.9.0+cu111",
      "import_names": ["torch"]
    },
    {
      "name": "pmdarima",
      "version": "1.8.5",
      "import_names": ["pmdarima"]
    },
    {
      "name": "sympy",
      "version": "1.13.3",
      "import_names": ["sympy"]
    },
    {
      "name": "einops",
      "version": "0.3.2",
      "import_names": ["einops"]
    },
    {
      "name": "fbm",
      "version": "0.3.0",
      "import_names": ["fbm"]
    }
  ],
  "evidence": {
    "source_roots": ["exp", "data_provider", "models", "layers", "utils", "FEDformer", "Pyraformer"],
    "docs": ["README.md", "LTSF-Benchmark.md"],
    "examples": ["scripts"],
    "tests": [],
    "configs": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and refresh it.
- If the current working tree is dirty and this snapshot was clean, or the dirty
  paths differ, refresh it.
- If the public CLI surface or dependency surface changes, refresh it even on
  the same commit.
