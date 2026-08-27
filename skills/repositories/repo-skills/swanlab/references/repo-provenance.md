# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of SwanLab. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:05:51Z",
  "repository": {
    "name": "SwanLab",
    "remote_url": "https://github.com/SwanHubX/SwanLab.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6d50bc3dd2ff16a76618755e8f857442c215f808",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"],
    "dirty_note": "Generated production artifacts were untracked under skills/ during skill creation and were excluded from source evidence."
  },
  "packages": [
    {
      "name": "swanlab",
      "version": "0.9.0-dev",
      "installed_distribution_version_seen_during_inspection": "0.9.0.dev0",
      "import_names": ["swanlab"]
    }
  ],
  "evidence": {
    "source_roots": ["swanlab/"],
    "docs": ["README.md", "README_EN.md", "docs/skills/"],
    "tests": ["tests/unit/"],
    "scripts": ["scripts/generate_protos.py", "scripts/clean_pycache.sh", "Makefile"],
    "protocol": ["protos/", "swanlab/proto/", "core/proto/"],
    "supporting_roots": ["core/"]
  },
  "construction_policy": {
    "extraction_scope": "agent-confirmed",
    "import_after_verification": "not-import"
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ materially from `dirty_paths`, inspect whether the changed files alter public SwanLab behavior and refresh when needed.
- If package metadata, public exports, CLI commands, optional extras, or major tests changed even on the same commit, refresh this skill.
- If a future task requires rich media, dashboard, S3, real cloud upload, self-hosted admin, or accelerator/framework training verification beyond the current snapshot, extend or refresh the skill with that backend-specific evidence.
