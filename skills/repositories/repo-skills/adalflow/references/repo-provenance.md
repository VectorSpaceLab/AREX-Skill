# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an AdalFlow checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:02:23Z",
  "repository": {
    "name": "AdalFlow",
    "remote_url": "https://github.com/SylphAI-Inc/AdalFlow.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "810de99d86191b3aa0c939aa6d6d1a21977555aa",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "adalflow",
      "version": "1.1.1",
      "import_names": ["adalflow"]
    }
  ],
  "evidence": {
    "source_roots": [
      "adalflow/adalflow/core",
      "adalflow/adalflow/components",
      "adalflow/adalflow/eval",
      "adalflow/adalflow/optim",
      "adalflow/adalflow/tracing",
      "adalflow/adalflow/datasets",
      "adalflow/adalflow/utils",
      "adalflow/adalflow/database",
      "adalflow/adalflow/apps"
    ],
    "docs": [
      "README.md",
      "adalflow/README.md",
      "docs/source/tutorials",
      "docs/source/new_tutorials",
      "docs/source/use_cases",
      "docs/source/design"
    ],
    "examples": [
      "tutorials",
      "use_cases",
      "benchmarks"
    ],
    "tests": ["adalflow/tests"],
    "configs": [
      "adalflow/pyproject.toml",
      "pyproject.toml",
      "use_cases/configs"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public imports, provider extras, or major docs/examples changed, refresh even on the same commit.
- The snapshot was generated from a dirty checkout because the repository had `skills/` production artifacts. Ignore a difference that is only regenerated skill/review output; refresh for source, docs, tests, package metadata, or public workflow changes.
- Do not compare against private environment paths. This provenance intentionally records only public repository and package facts.
