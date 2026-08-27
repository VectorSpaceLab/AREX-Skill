# Repository Provenance

## Purpose

Read this before deciding whether this FastReID skill is current for a checkout
of the repository. If the current repo commit, dirty state, package version, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T14:07:47Z",
  "repository": {
    "name": "fast-reid",
    "remote_url": "https://github.com/JDAI-CV/fast-reid.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "c9bc3ceb2f7a6438b62fb515ea3df6d1e999e95d",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "fastreid-source-only",
      "version": "1.3",
      "import_names": ["fastreid"],
      "distribution_metadata": "not available in this checkout; no setup.py or pyproject.toml"
    }
  ],
  "evidence": {
    "source_roots": ["fastreid/"],
    "docs": ["README.md", "INSTALL.md", "GETTING_STARTED.md", "MODEL_ZOO.md", "CHANGELOG.md", "docs/"],
    "configs": ["configs/"],
    "datasets": ["datasets/README.md"],
    "examples": ["demo/", "tools/", "tools/deploy/", "projects/"],
    "tests": ["tests/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has source changes outside generated skill or
  review artifacts, run `refresh-repo-skill`.
- If FastReID gains packaging metadata, entry points, different config keys, or
  changed public registry names, refresh the skill even if the commit is the
  same.
- If deployment dependencies or project extension APIs change, refresh the
  `deployment-and-projects` sub-skill before relying on export/project guidance.
