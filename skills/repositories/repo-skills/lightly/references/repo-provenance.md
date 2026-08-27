# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:56:55Z",
  "repository": {
    "name": "lightly",
    "remote_url": "https://github.com/lightly-ai/lightly.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "483f80923c6ffd47c7f0fedab98e3d46d873a27b",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "lightly",
      "version": "1.5.26",
      "import_names": [
        "lightly"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "lightly"
    ],
    "docs": [
      "README.md",
      "docs/source"
    ],
    "examples": [
      "examples/pytorch",
      "examples/pytorch_lightning",
      "examples/pytorch_lightning_distributed"
    ],
    "tests": [
      "tests"
    ],
    "configs": [
      "lightly/cli/config/config.yaml",
      "pyproject.toml",
      "Makefile"
    ],
    "maintenance": [
      "CONTRIBUTING.md",
      "MAINTAINING.md",
      "CLAUDE.md",
      ".github/workflows"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from this snapshot, run `refresh-repo-skill`.
- If package metadata, console entry points, optional extras, examples, or public APIs changed even on the same commit, run `refresh-repo-skill`.
