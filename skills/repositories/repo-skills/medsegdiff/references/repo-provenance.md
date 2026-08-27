# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a MedSegDiff
checkout. If the current commit, dirty state, requirements, public scripts, or
source layout differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T19:14:18Z",
  "repository": {
    "name": "MedSegDiff",
    "remote_url": "https://github.com/ImprintLab/MedSegDiff.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "28b343fddd6bb6dc1bccdaed94ca7ebefe9142f3",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["guided_diffusion"]
    }
  ],
  "evidence": {
    "source_roots": ["guided_diffusion"],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": ["requirement.txt", "data/isic_csv"],
    "scripts": [
      "scripts/segmentation_train.py",
      "scripts/segmentation_sample.py",
      "scripts/segmentation_env.py",
      "scripts/segmentation_env_PerClass.py"
    ]
  }
}
```

## Notes on package identity

The source checkout has no `pyproject.toml`, `setup.py`, `setup.cfg`, package
version, console entry point, or lockfile. The top-level import root is
`guided_diffusion`; no upstream distribution name or release version was
available. Public runtime dependencies are listed in `requirement.txt`.

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- This snapshot was created from a checkout dirty only because generated
  `skills/` artifacts were present. If other source paths are dirty, or the
  set of dirty paths differs materially, refresh the skill.
- Refresh if public scripts, loader contracts, model factory defaults,
  dependency requirements, checkpoints, or entry points changed even when the
  commit appears unchanged.
