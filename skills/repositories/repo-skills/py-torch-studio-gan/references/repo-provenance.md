# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PyTorch-StudioGAN. If the current repo commit, dirty state, package/script entry points, configs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:17:51Z",
  "repository": {
    "name": "PyTorch-StudioGAN",
    "remote_url": "https://github.com/POSTECH-CVLab/PyTorch-StudioGAN.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "947b35e9835b67860fdce44d337f6d7fee7c8db3",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "config",
        "data_util",
        "main",
        "evaluate",
        "models",
        "metrics",
        "utils"
      ],
      "note": "No pyproject.toml, setup.py, setup.cfg, requirements file, or installed distribution metadata was present; StudioGAN is operated as a script-first checkout."
    }
  ],
  "evidence": {
    "source_roots": [
      "src"
    ],
    "docs": [
      "README.md",
      "src/configs/StyleGAN_ADA_GuideLine.md"
    ],
    "examples": [],
    "tests": [
      "src/sync_batchnorm/unittest.py"
    ],
    "configs": [
      "src/configs"
    ],
    "entry_points": [
      "src/main.py",
      "src/evaluate.py"
    ],
    "reference_only": [
      "logs",
      "docs/figures"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If the current checkout's public scripts, `src/config.py`, `src/configs/`, `src/models/`, `src/metrics/`, or `src/utils/` changed substantially, refresh even if a task only asks for one workflow.
- If a future version adds package metadata, console entry points, requirements files, new metric backbones, new config schemas, or changed checkpoint naming, refresh before using older command builders.
- The dirty path recorded here is the local generated `skills/`/production artifact area. It is not source evidence for StudioGAN runtime behavior.
