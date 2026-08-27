# Repository Provenance

## Purpose

Read this before deciding whether this Argilla skill is current for a checkout. If the current repo commit, package versions, dirty state, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:46:58Z",
  "repository": {
    "name": "argilla",
    "remote_url": "https://github.com/argilla-io/argilla.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "5338519accb13ae422f8bf9c0642651c249c49af",
    "working_tree": "clean at source analysis before generated skill outputs were written",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "argilla",
      "version": "2.8.0dev0",
      "import_names": ["argilla"]
    },
    {
      "name": "argilla-server",
      "version": "2.8.0dev0",
      "import_names": ["argilla_server"]
    },
    {
      "name": "argilla-v1",
      "version": "1.29.1",
      "import_names": ["argilla_v1", "argilla.v1"]
    }
  ],
  "evidence": {
    "source_roots": [
      "argilla/src/argilla",
      "argilla-server/src/argilla_server",
      "argilla-v1/src/argilla_v1"
    ],
    "package_metadata": [
      "argilla/pyproject.toml",
      "argilla-server/pyproject.toml",
      "argilla-v1/pyproject.toml"
    ],
    "docs": [
      "README.md",
      "argilla/docs/getting_started",
      "argilla/docs/how_to_guides",
      "argilla/docs/reference/argilla",
      "argilla/docs/reference/argilla-server",
      "docs/migration-rubrix.md"
    ],
    "examples": [
      "examples/deployments",
      "examples/webhooks/basic-webhooks"
    ],
    "tests": [
      "argilla/tests/unit",
      "argilla/tests/integration",
      "argilla-server/tests/unit"
    ],
    "selected_exclusions": [
      "argilla-frontend",
      "most docs/_source legacy notebooks",
      "deep argilla-v1 optional training/monitoring integrations",
      "repository CI/release/docs-generation internals"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public SDK signatures, server CLI help, server config variables, or migration docs changed, refresh even on the same commit.
- If current work depends on frontend internals, repo maintenance, or old optional v1 training/monitoring integrations, this skill does not cover that scope; create/extend a separate skill instead of stretching this one.
- Generated skill files and review artifacts are not part of the source evidence snapshot above.
