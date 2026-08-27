# Repository Provenance

## Purpose

Read this before deciding whether the nuPlan skill is current for a checkout or
installation. If the source commit, package version, public entry points, or
major evidence paths differ, run a refresh/review before relying on detailed
claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T20:00:00Z",
  "repository": {
    "name": "nuplan-devkit",
    "remote_url": "https://github.com/motional/nuplan-devkit",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "e9241677997ddf86b0bcd44817ab04fe631405b",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "nuplan-devkit",
      "version": "1.2.2",
      "import_names": ["nuplan"]
    }
  ],
  "entry_points": ["nuplan_cli = nuplan.cli.nuplan_cli:main"],
  "evidence": {
    "source_roots": ["nuplan/common", "nuplan/database", "nuplan/planning", "nuplan/submission", "nuplan/cli"],
    "docs": ["docs/installation.md", "docs/dataset_setup.md", "docs/nuplan_schema.md", "docs/baselines.md", "docs/competition.md", "docs/nuplan_submission_tutorial.md", "docs/faq.md"],
    "examples": ["tutorials/nuplan_framework.ipynb", "tutorials/nuplan_planner_tutorial.ipynb", "tutorials/nuplan_advanced_model_training.ipynb", "tutorials/nuplan_scenario_visualization.ipynb"],
    "tests": ["nuplan/**/test", "nuplan/**/tests", "tutorials/test"],
    "configs": ["nuplan/planning/script/config", "nuplan/planning/script/experiments"]
  }
}
```

## Refresh check

- If the current commit differs from `e9241677997ddf86b0bcd44817ab04fe631405b`,
  treat this skill as potentially stale.
- Recheck the package version and `nuplan_cli` entry point after dependency or
  packaging changes.
- Recheck Hydra config names and the data layout after changes under the
  planning script configuration or dataset schema.
- Recheck the submission contract after any protocol, launcher, or container
  change. Never infer organizer compatibility from a successful local import.
