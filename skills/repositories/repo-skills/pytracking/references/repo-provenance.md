# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PyTracking. If the current repo commit, dirty state, package/import behavior, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:48:23Z",
  "repository": {
    "name": "pytracking",
    "remote_url": "https://github.com/visionml/pytracking.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "7eb9e74bd3d40e29dbcec444902237da13de247b",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["pytracking", "ltr"],
      "metadata_note": "This snapshot has no pyproject.toml, setup.py, or setup.cfg; PyTracking/LTR are source-root packages."
    },
    {
      "name": "torch",
      "version": "2.13.0",
      "import_names": ["torch"],
      "verification_note": "Inspection environment CUDA smoke passed; exact user runtime may differ."
    }
  ],
  "evidence": {
    "source_roots": ["pytracking", "ltr"],
    "docs": ["README.md", "INSTALL.md", "INSTALL_win.md", "MODEL_ZOO.md", "pytracking/README.md", "ltr/README.md"],
    "runtime_entry_points": ["pytracking/run_tracker.py", "pytracking/run_video.py", "pytracking/run_webcam.py", "pytracking/run_experiment.py", "pytracking/run_vot.py"],
    "training_entry_points": ["ltr/run_training.py", "ltr/train_settings"],
    "analysis_and_packaging": ["pytracking/analysis", "pytracking/util_scripts", "pytracking/VOT", "pytracking/notebooks"],
    "configuration": ["pytracking/evaluation/environment.py", "ltr/admin/environment.py", "ltr/data_specs"],
    "tracker_development": ["pytracking/tracker", "pytracking/parameter", "pytracking/features", "pytracking/libs", "pytracking/utils"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from this snapshot, check whether source/docs/config files changed before trusting workflow details.
- If package metadata, import behavior, CLI arguments, tracker parameter files, training settings, or dataset aliases changed, refresh this skill.
- This skill deliberately excludes generated/user-local files, downloaded checkpoints/results, full datasets, and private inspection environment paths from provenance.
