# Repository Provenance

Read this before deciding whether the OpenCDA skill matches a checkout. If the
commit, package version, dirty state, or major evidence paths differ, run a
repo-skill refresh before relying on detailed claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T18:58:07Z",
  "repository": {
    "name": "OpenCDA",
    "remote_url": "https://github.com/ucla-mobility/OpenCDA.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "72b17e7b7fa0d67da1bf11a4083c90737eb1225f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/disco/opencda", "skills/tests/opencda"]
  },
  "packages": [
    {
      "name": "OpenCDA",
      "version": "0.1.3",
      "import_names": ["opencda"]
    },
    {
      "name": "carla",
      "version": "0.9.12 client verified for inspection",
      "import_names": ["carla"]
    }
  ],
  "evidence": {
    "source_roots": ["opencda", "opencda/core", "opencda/co_simulation", "opencda/customize", "opencda/scenario_testing"],
    "docs": ["README.md", "docs/md_files/installation.md", "docs/md_files/getstarted.md", "docs/md_files/yaml_define.md", "docs/md_files/logic_flow.md", "docs/md_files/traffic_generation.md", "docs/md_files/developer_tutorial.md", "docs/md_files/customization.md"],
    "examples": ["opencda/scenario_testing/*.py", "opencda/scenario_testing/config_yaml/*.yaml"],
    "tests": ["test/test_kf.py", "test/test_ekf.py", "test/test_sensor_transformation.py", "test/test_drive_profile_plotting.py", "test/test_localization_debug_helper.py", "test/test_planer_debug_helper.py", "test/test_ml_manager.py"],
    "configs": ["requirements.txt", "requirements_ci.txt", "environment.yml", "Dockerfile", "opencda/scenario_testing/config_yaml/default.yaml", "opencda/scenario_testing/config_yaml/*.yaml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale.
- If the dirty paths differ materially or the generated skill was copied to a
  checkout with changed source, refresh it before making version-specific API
  claims.
- If package metadata, supported CARLA versions, scenario names, public entry
  points, YAML schema, or core manager signatures changed, refresh the relevant
  sub-skill even if the commit appears unchanged.
- The generated skill deliberately omits large maps/images, model weights,
  simulator binaries, and external SUMO/ScenarioRunner installations. Their
  presence or absence is a runtime prerequisite, not evidence that this skill
  is stale.
