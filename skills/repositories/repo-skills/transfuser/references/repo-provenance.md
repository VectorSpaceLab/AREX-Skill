# Repository Provenance

Read this before deciding whether the skill is current for a TransFuser checkout.
If the source commit, dirty state, dependency contract, or major evidence paths
differ, use a refresh workflow before relying on detailed claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T00:40:00Z",
  "repository": {
    "name": "transfuser",
    "remote_url": "https://github.com/autonomousvision/transfuser",
    "vcs": "git",
    "branch": "2022",
    "tag": null,
    "commit": "9d413b2ad2d2d56c112b34a4a799be081800d77f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/transfuser.log"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["team_code_transfuser modules", "leaderboard", "scenario_runner"]
    }
  ],
  "evidence": {
    "source_roots": ["team_code_transfuser", "team_code_autopilot", "leaderboard/leaderboard", "tools"],
    "docs": ["README.md", "leaderboard/README.md", "leaderboard/data/longest6/README.md", "tools/dataset/README.md", "team_code_autopilot/README.md"],
    "examples": ["leaderboard/scripts/local_evaluation.sh", "leaderboard/scripts/datagen.sh", "leaderboard/scripts/run_evaluation.sh"],
    "tests": [],
    "configs": ["environment.yml", "team_code_transfuser/requirements.txt", "leaderboard/data/training", "leaderboard/data/longest6"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- Check whether the source tree's dirty paths differ from the snapshot.
- Reinspect `team_code_transfuser/requirements.txt`, model/data/config APIs,
  CARLA version pins, route/scenario schemas, and evaluation scripts when they
  change.
- This repository has no Python packaging metadata for a normal installed
  distribution; the source modules are imported with a checkout-aware
  `PYTHONPATH` during legacy workflows.
