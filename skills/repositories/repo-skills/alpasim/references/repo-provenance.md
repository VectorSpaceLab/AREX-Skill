# Repository Provenance

Read this before deciding whether the AlpaSim skill matches a checkout. If the
commit, dirty state, package versions, public entry points, or major evidence
paths differ, run `refresh-repo-skill` before relying on detailed guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T19:32:02Z",
  "repository": {
    "name": "alpasim",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "affc2eab209fa43bdfa2f26c0f8d437922d78a68",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "alpasim_wizard", "version": "0.0.1", "import_names": ["alpasim_wizard"]},
    {"name": "alpasim-runtime", "version": "1.158.0", "import_names": ["alpasim_runtime"]},
    {"name": "alpasim_grpc", "version": "0.55.0", "import_names": ["alpasim_grpc"]},
    {"name": "alpasim_utils", "version": "0.52.0", "import_names": ["alpasim_utils"]},
    {"name": "alpasim_eval", "version": "1.36.0", "import_names": ["eval"]},
    {"name": "alpasim_controller", "version": "0.89.0", "import_names": ["alpasim_controller"]},
    {"name": "alpasim-physics", "version": "1.84.0", "import_names": ["alpasim_physics"]},
    {"name": "alpasim-trafficsim", "version": "0.2.0", "import_names": ["alpasim_trafficsim"]},
    {"name": "alpasim_driver", "version": "0.91.0", "import_names": ["alpasim_driver"]},
    {"name": "alpasim_plugins", "version": "0.1.0", "import_names": ["alpasim_plugins"]},
    {"name": "utils_rs", "version": "0.1.0", "import_names": ["utils_rs"]}
  ],
  "evidence": {
    "source_roots": [
      "src/wizard/alpasim_wizard",
      "src/runtime/alpasim_runtime",
      "src/grpc/alpasim_grpc",
      "src/utils/alpasim_utils",
      "src/eval/src/eval",
      "src/controller/alpasim_controller",
      "src/physics/alpasim_physics",
      "src/trafficsim/alpasim_trafficsim",
      "src/driver/src/alpasim_driver",
      "src/plugins/alpasim_plugins",
      "plugins/transfuser_driver/alpasim_transfuser"
    ],
    "docs": ["README.md", "docs", "data/scenes/README.md", "src/*/README.md", "AGENTS.md", "CONTRIBUTING.md"],
    "examples": ["docs/TUTORIAL.md", "docs/MANUAL_DRIVER.md", "docs/VIDEO_MODEL.md", "src/controller/benchmark"],
    "tests": ["src/*/tests", "plugins/transfuser_driver/tests"],
    "configs": ["src/wizard/configs", "src/trafficsim/alpasim_trafficsim/config", "src/driver/configs"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the commit above, treat the skill as
  stale and run `refresh-repo-skill`.
- This snapshot was generated from a dirty checkout whose only observed dirty
  path was the production `skills/` tree. If source files, package manifests,
  docs, configs, or tests become dirty, refresh before trusting exact claims.
- If package versions or public entry points change, refresh even when the
  commit is unchanged.
