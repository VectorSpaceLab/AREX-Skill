# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill` before using
these instructions as authoritative.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:23:51Z",
  "repository": {
    "name": "electricitymaps-contrib",
    "remote_url": "https://github.com/electricitymaps/electricitymaps-contrib.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "db11e59fd0afdfeb293a2ed30ed7235b8f94bf1b",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "electricitymap-contrib",
      "version": "2.7.1",
      "import_names": ["electricitymap.contrib", "test_parser", "capacity_update"]
    },
    {
      "name": "electricitymap-contrib-types",
      "version": "1.6.0",
      "import_names": ["electricitymap.contrib.types"]
    }
  ],
  "evidence": {
    "source_roots": [
      "electricitymap/contrib/parsers",
      "electricitymap/contrib/parsers/lib",
      "electricitymap/contrib/capacity_parsers",
      "electricitymap/contrib/config",
      "electricitymap/contrib/lib",
      "libs/types/src/electricitymap/contrib/types"
    ],
    "docs": [
      "README.md",
      "CONTRIBUTING.md",
      "electricitymap/contrib/parsers/README.md",
      "electricitymap/contrib/parsers/examples/production.md",
      "electricitymap/contrib/capacity_parsers/README.md"
    ],
    "scripts": [
      "test_parser.py",
      "capacity_update.py",
      "scripts/tooling.py",
      "scripts/update_capacity_configuration.py",
      "scripts/validate_config_filenames.py",
      "scripts/create_aggregated_zone_config.py",
      "scripts/remove_zone.py",
      "scripts/zone_names.py",
      "scripts/update_capacity_ember_all_years.py",
      "scripts/ENTSOE_capacity_update.py"
    ],
    "tests": [
      "tests/test_parser_interface.py",
      "electricitymap/contrib/parsers/tests",
      "tests/test_capacity.py",
      "tests/test_update_capacity_configuration.py",
      "electricitymap/contrib/capacity_parsers/tests",
      "tests/config",
      "tests/test_zones_json.py",
      "tests/test_exchanges_json.py",
      "tests/test_co2eq_parameters.py"
    ],
    "configs": [
      "config/zones",
      "config/exchanges",
      "config/defaults.yaml",
      "config/data_centers/data_centers.json",
      "geo/world.geojson"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale.
- If `pyproject.toml` changes package version, extras, dependency groups,
  console scripts, or pytest paths, refresh the skill.
- If parser data types, parser/config model fields, capacity update helpers, or
  config file layouts change, refresh the relevant sub-skill before making
  operational claims.
- The snapshot was generated from a dirty checkout because `skills/` already
  contained production artifacts/logs and now contains this generated skill.
  A future refresh should compare only meaningful repo-code/config changes, not
  regenerated review artifacts.
