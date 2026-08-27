# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T07:12:51Z",
  "repository": {
    "name": "vit-pytorch",
    "remote_url": "https://github.com/lucidrains/vit-pytorch.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "bb13e27ee5b30ddd3e09c2e23c30ec2c17683d35",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "vit-pytorch",
      "version": "1.24.2",
      "import_names": ["vit_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["vit_pytorch"],
    "docs": ["README.md"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ materially from this snapshot,
  run `refresh-repo-skill`.
- If package metadata, public import names, or user-facing workflows changed
  even on the same commit, run `refresh-repo-skill`.
