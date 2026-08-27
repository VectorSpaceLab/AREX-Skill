# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Humanoid-Gym. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T14:42:24Z",
  "repository": {
    "name": "humanoid-gym",
    "remote_url": "https://github.com/roboterax/humanoid-gym.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v1.0.0",
    "commit": "ae46e201c85a2b17e7f2cea59a441dae7ea88a8f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "humanoid",
      "version": "1.0.0",
      "import_names": ["humanoid"]
    }
  ],
  "evidence": {
    "source_roots": ["humanoid/"],
    "docs": ["README.md"],
    "examples": ["humanoid/scripts/train.py", "humanoid/scripts/play.py", "humanoid/scripts/sim2sim.py"],
    "tests": [],
    "configs": ["setup.py", "humanoid/envs/custom/humanoid_config.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
