# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the SDV repository. If the current repo commit, dirty state, package version, public import surface, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:02:17Z",
  "repository": {
    "name": "SDV",
    "remote_url": null,
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "461537559cd54ec769226738dfba6fbb114a3709",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "sdv",
      "version": "1.38.1.dev0",
      "import_names": ["sdv"]
    }
  ],
  "evidence": {
    "source_roots": [
      "sdv/"
    ],
    "docs": [
      "README.md",
      "EVALUATION.md",
      "HISTORY.md",
      "docs/index.rst"
    ],
    "package_metadata": [
      "pyproject.toml",
      "requirements.txt",
      "latest_requirements.txt",
      "apt.txt"
    ],
    "verification_sources": [
      "selected unit-test evidence summarized in verification artifacts",
      "selected integration-test evidence summarized in verification artifacts"
    ],
    "excluded_from_runtime_skill": [
      "repository maintainer/release scripts",
      "repository test fixtures and generated verification artifacts"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package source under `sdv/`, package metadata, public docs, or relevant verification evidence changes, run `refresh-repo-skill`.
- If the current checkout gains a real `sdv/cli` package, refresh routing and troubleshooting because this generated skill intentionally treats SDV as API-first.
- If package metadata or public constructor/function signatures changed, refresh before relying on API-reference details.
- The dirty path in this snapshot is the generated `skills/` output area; it is not a source-code modification to SDV itself.
