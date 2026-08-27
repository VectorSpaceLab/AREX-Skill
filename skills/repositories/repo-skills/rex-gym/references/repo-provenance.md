# Repository Provenance

## Purpose

Read this before deciding whether the skill is current for a checkout of
Rex-Gym. If the commit, dirty state, package version, public entry points, or
major evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T09:20:00Z",
  "repository": {
    "name": "rex-gym",
    "remote_url": "https://github.com/nicrusso7/rex-gym.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "26663048bd3c3da307714da4458b1a2a9dc81824",
    "working_tree": "dirty",
    "dirty_paths": ["skills/ (untracked production and review artifacts at generation time)"]
  },
  "packages": [
    {
      "name": "rex_gym",
      "version": "0.2.7",
      "import_names": ["rex_gym"]
    }
  ],
  "evidence": {
    "source_roots": ["rex_gym"],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": ["setup.py", "setup.cfg", "requirements.txt", "rex_gym/policies/**/config.yaml"],
    "scripts": ["rex_gym/cli/entry_point.py", "rex_gym/playground/trainer.py", "rex_gym/playground/policy_player.py"]
  }
}
```

## Refresh Check

- If the checkout's `git rev-parse HEAD` differs from the commit above, treat
  this graph as potentially stale.
- If the working tree becomes clean or its changed paths differ materially,
  refresh the graph before relying on version-sensitive guidance.
- Refresh if `setup.py`, `requirements.txt`, the Click entry point, environment
  classes, model helpers, PPO config modules, policy mapping, or packaged URDF
  data changes.
- The source has no formal test/example directory; changes to documented CLI
  workflows or package data are also refresh signals.
