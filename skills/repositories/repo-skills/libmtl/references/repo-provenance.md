# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T23:37:34Z",
  "repository": {
    "name": "LibMTL",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4336804847eaa5e0b924b743d76beec7ac3fdc97",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "LibMTL",
      "version": "1.1.5",
      "import_names": ["LibMTL"]
    }
  ],
  "evidence": {
    "source_roots": ["LibMTL"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "requirements.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was clean and the current working tree differs, run
  `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit,
  run `refresh-repo-skill`.

## Staleness Notes

- Several docs and tests still mention `train_nyu.py`, `train_office.py`,
  `train_qm9.py`, and `train_pawsx.py`, but the current checkout exposes the
  example entry points as `examples/*/main.py`.
- The PAWS-X raw preprocessing code under `examples/xtreme/propocess_data/`
  still contains legacy `networkx` assumptions; treat it as compatibility
  sensitive.
