# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Flow Forecast. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the operating guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:09:09Z",
  "repository": {
    "name": "flow-forecast",
    "remote_url": "https://github.com/AIStream-Peelout/flow-forecast.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "304cf30eb1e1007f572fca5d63083c2d25a4e3ec",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "flood_forecast",
      "normalized_distribution_names": ["flood-forecast", "flood_forecast"],
      "version": "1.1.dev0",
      "source_setup_version": "1.001dev",
      "import_names": ["flood_forecast"]
    }
  ],
  "evidence": {
    "source_roots": [
      "flood_forecast/",
      "flood_forecast/basic/",
      "flood_forecast/custom/",
      "flood_forecast/da_rnn/",
      "flood_forecast/deployment/",
      "flood_forecast/meta_models/",
      "flood_forecast/multi_models/",
      "flood_forecast/ode/",
      "flood_forecast/preprocessing/",
      "flood_forecast/transformer_xl/"
    ],
    "docs": ["README.md", "docs/source/", "flood_forecast/da_rnn/README.md"],
    "examples_and_scripts": ["_narx_smoke.py", "build_narx_notebook.py", "NARX_Virgin_Predict.ipynb"],
    "tests": ["tests/", ".circleci/config.yml"],
    "configs": ["tests/*.json", "requirements.txt", "setup.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If source files, package metadata, public model registry keys, loader APIs, or training/inference config behavior changed, refresh even when the commit hash is the same.
- Dirty paths in this snapshot are generated skill artifacts. If a future checkout has source-code dirty paths outside `skills/`, refresh before trusting source-derived claims.
- If package installation resolves a substantially different distribution version or dependency set, rerun the environment/import checks in the root script and refresh if signatures or registry keys changed.
