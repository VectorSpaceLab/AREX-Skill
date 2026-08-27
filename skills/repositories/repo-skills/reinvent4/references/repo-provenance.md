# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of REINVENT4. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T19:38:24Z",
  "repository": {
    "name": "REINVENT4",
    "remote_url": "https://github.com/MolecularAI/REINVENT4",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "04de385d33f95e97f3960b5c4184a0c0bd3ad7f8",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "reinvent",
      "version": "4.8.24",
      "import_names": ["reinvent", "reinvent_plugins"]
    }
  ],
  "evidence": {
    "source_roots": ["reinvent", "reinvent_plugins"],
    "docs": ["README.md", "configs/README.md", "configs/PARAMS.md", "configs/SCORING.md", "contrib/reinvent-doc/tutorials"],
    "examples": ["configs", "notebooks"],
    "tests": ["tests"],
    "configs": ["configs/sampling.toml", "configs/scoring.toml", "configs/transfer_learning.toml", "configs/staged_learning.toml", "configs/data_pipeline.toml", "configs/enumeration.toml"],
    "scripts": ["install.py", "configs/toml2json.py", "support"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from `repository.dirty_paths`, review whether changes affect public package behavior or skill evidence.
- If `pyproject.toml`, console entry points, config schemas, run modes, scoring components, or plugin discovery rules changed, refresh this skill even when the commit is unchanged.
- If package version `reinvent` differs from `4.8.24`, verify CLI help, config validators, and optional dependency guidance again.
