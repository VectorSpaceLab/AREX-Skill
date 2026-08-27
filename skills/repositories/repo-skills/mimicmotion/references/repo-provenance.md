# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T17:45:00Z",
  "repository": {
    "name": "MimicMotion",
    "remote_url": "https://github.com/Tencent/MimicMotion.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6907bdcc259a6a048d41a365e840d22274f9256c",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mimicmotion",
      "version": null,
      "import_names": ["mimicmotion"]
    }
  ],
  "evidence": {
    "source_roots": ["mimicmotion"],
    "docs": ["README.md"],
    "examples": ["assets/example_data"],
    "tests": [],
    "configs": ["configs/test.yaml", "environment.yaml", "cog.yaml"],
    "entry_points": ["inference.py", "predict.py"],
    "other": ["constants.py", "LICENSE"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, dependencies, checkpoint names, CLI flags, config schema, or public entry points changed even on the same commit, run `refresh-repo-skill`.
