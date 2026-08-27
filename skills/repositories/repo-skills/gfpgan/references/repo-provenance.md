# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches the current GFPGAN checkout. If the commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T14:56:56Z",
  "repository": {
    "name": "GFPGAN",
    "remote_url": "https://github.com/TencentARC/GFPGAN.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "7552a7791caad982045a7bbe5634bbf1cd5c8679",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "gfpgan",
      "version": "1.3.8",
      "import_names": ["gfpgan"]
    }
  ],
  "evidence": {
    "source_roots": ["gfpgan"],
    "docs": ["README.md", "README_CN.md", "FAQ.md", "Comparisons.md", "PaperModel.md"],
    "examples": ["inference_gfpgan.py", "inputs"],
    "tests": ["tests"],
    "configs": ["options", "cog.yaml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the working tree becomes dirty or the dirty paths change, refresh the skill.
- If package metadata, public entry points, or checkpoint/model names change, refresh the skill.
