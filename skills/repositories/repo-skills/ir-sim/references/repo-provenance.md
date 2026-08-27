# Repository Provenance

Read this before deciding whether the IR-SIM operating graph still matches a
checkout. If the commit, dirty state, package version, public entry points, or
major evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T19:36:54Z",
  "repository": {
    "name": "ir-sim",
    "remote_url": "https://github.com/hanruihua/ir-sim",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9fd4c9f3c612b7fcbb0d37ea27d8a5910c9ad4e",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "ir-sim",
      "version": "2.10.2",
      "import_names": ["irsim"]
    }
  ],
  "evidence": {
    "source_roots": [
      "irsim",
      "irsim/env",
      "irsim/world",
      "irsim/lib",
      "irsim/gui",
      "irsim/util"
    ],
    "docs": [
      "README.md",
      "docs/source/get_started",
      "docs/source/usage",
      "docs/source/yaml_config"
    ],
    "examples": ["usage/01empty_world through usage/24fog_world"],
    "tests": [
      "tests/test_env.py",
      "tests/test_geometry.py",
      "tests/test_kinematics.py",
      "tests/test_objects.py",
      "tests/test_sensors.py",
      "tests/test_world_map.py",
      "tests/test_behaviors.py",
      "tests/test_sfm.py",
      "tests/test_rvo_line_obstacles.py",
      "tests/test_path_planners.py",
      "tests/test_plot.py",
      "tests/test_util.py",
      "tests/test_gui.py"
    ],
    "configs": ["pyproject.toml", "uv.lock", "usage/**/*.yaml", "tests/**/*.yaml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this graph as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty, or the dirty paths differ from the
  recorded snapshot, refresh before relying on source-sensitive claims.
- If `pyproject.toml` changes the package version, Python floor, dependencies,
  optional extras, public entry points, or package-data rules, refresh.
- If the public YAML schema, environment factory, sensor payloads, behavior
  registry, planner constructors, or map generator registry changes, refresh the
  owning sub-skill even when the commit remains otherwise familiar.

The snapshot identifies evidence relative to the repository root only. The
private inspection environment and review/test records used during construction
are not part of this runtime graph.
