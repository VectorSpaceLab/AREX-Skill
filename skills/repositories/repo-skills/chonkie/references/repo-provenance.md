# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, tag, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill for new code.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:55:00Z",
  "repository": {
    "name": "chonkie",
    "remote_url": "https://github.com/feyninc/chonkie.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v1.7.0",
    "commit": "0a6baea1a42c9afe9b3bc31ecb37739e744bb1ec",
    "working_tree": "dirty-untracked-skill-production-artifacts-excluded",
    "dirty_paths": ["skills/chonkie.log"]
  },
  "packages": [
    {
      "name": "chonkie",
      "version": "1.7.0",
      "import_names": ["chonkie"],
      "console_scripts": ["chonkie = chonkie.cli:main"],
      "requires_python": ">=3.10"
    }
  ],
  "evidence": {
    "source_roots": ["src/chonkie"],
    "docs": [
      "README.md",
      "docs/content/docs/chonkie/installation.mdx",
      "docs/content/docs/chonkie/quick-start.mdx",
      "docs/content/docs/chonkie/pipelines.mdx",
      "docs/content/docs/chonkie/troubleshooting.mdx"
    ],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "Dockerfile", "docker-compose.yml"],
    "excluded_from_runtime_dependency": [
      "source repository tests and docs",
      "docs-site build plumbing",
      "assets",
      "lock/cache/build outputs",
      "generated skill/review artifacts",
      "private inspection environment"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current package version, public imports, console entry points, or optional extras differ from the snapshot, refresh.
- If source paths under `src/chonkie`, public docs, tests, or packaging metadata changed materially, refresh.
- Do not treat this generated skill tree itself as source evidence for Chonkie package behavior.
