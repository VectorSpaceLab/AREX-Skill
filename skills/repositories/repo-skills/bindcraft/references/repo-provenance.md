# Repository Provenance

Read this before deciding whether the skill is current for a BindCraft checkout.
If the commit, dirty paths, public entry points, or major evidence paths differ,
run the refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T00:00:00Z",
  "repository": {
    "name": "BindCraft",
    "remote_url": "https://github.com/martinpacesa/BindCraft.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "efb5bfeb8b4b1a5944256f979c34e0c8e6a82d9d",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "BindCraft",
      "version": null,
      "import_names": ["functions"]
    }
  ],
  "evidence": {
    "source_roots": ["bindcraft.py", "functions"],
    "docs": ["README.md"],
    "examples": ["example", "notebooks/BindCraft.ipynb"],
    "tests": [],
    "configs": ["settings_target", "settings_filters", "settings_advanced"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- If the checkout is dirty, compare the changed relative paths with the recorded
  baseline; generated skill and verification paths are expected production
  changes, while source changes require review.
- Recheck public CLI flags, JSON keys, dependency/install instructions, and the
  `functions/` APIs when BindCraft changes its pipeline or presets.
- This repository has no package metadata file or native test directory in the
  captured revision; source and README evidence are the primary baseline.
