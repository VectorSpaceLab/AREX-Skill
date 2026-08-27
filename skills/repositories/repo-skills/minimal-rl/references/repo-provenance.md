# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T17:52:44Z",
  "repository": {
    "name": "minimalRL",
    "remote_url": "https://github.com/seungeunrho/minimalRL.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "c8efed8481e3cd40e9739cfde220a55522555b57",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "minimalRL",
      "version": null,
      "import_names": [],
      "note": "Repository is a collection of top-level Python scripts, not an installable Python distribution."
    }
  ],
  "dependencies": [
    {
      "name": "torch",
      "version_checked": "2.13.0",
      "role": "PyTorch tensor/model backend for all scripts"
    },
    {
      "name": "gym",
      "version_checked": "0.26.2",
      "role": "CartPole-v1 and Pendulum-v1 environments used by the scripts"
    },
    {
      "name": "numpy",
      "version_checked": "1.26.4",
      "role": "Array and noise utility dependency; kept below 2 for Gym 0.26 compatibility"
    }
  ],
  "evidence": {
    "source_roots": [
      "REINFORCE.py",
      "actor_critic.py",
      "ppo.py",
      "ppo-lstm.py",
      "vtrace.py",
      "dqn.py",
      "acer.py",
      "a2c.py",
      "a3c.py",
      "ddpg.py",
      "ppo-continuous.py",
      "sac.py"
    ],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source changes outside generated `skills/` artifacts, run `refresh-repo-skill`.
- If the repository becomes an installable Python package, adds console entry points, changes Gym/Gymnasium support, or changes any algorithm script surfaces listed above, run `refresh-repo-skill`.
- If full native training behavior becomes a verification requirement, extend this skill with bounded native cases before relying on performance claims.
