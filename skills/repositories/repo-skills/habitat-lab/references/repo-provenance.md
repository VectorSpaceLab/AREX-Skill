# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Habitat-Lab. If the current repo commit, dirty state, package version, public entry points, config layout, or evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "repository": {
    "name": "habitat-lab",
    "remote_url": "https://github.com/facebookresearch/habitat-lab",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "0fb6f43ffe806a8088a171b036336c093bcf604e",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "habitat-lab",
      "version": "0.3.3",
      "import_names": ["habitat"]
    },
    {
      "name": "habitat-baselines",
      "version": "0.3.3",
      "import_names": ["habitat_baselines"]
    },
    {
      "name": "habitat-hitl",
      "version": "0.3.3",
      "import_names": ["habitat_hitl"]
    },
    {
      "name": "habitat-sim",
      "version": "0.3.3",
      "import_names": ["habitat_sim", "magnum"]
    }
  ],
  "evidence": {
    "source_roots": [
      "habitat-lab/habitat",
      "habitat-baselines/habitat_baselines",
      "habitat-hitl/habitat_hitl"
    ],
    "docs": [
      "README.md",
      "DATASETS.md",
      "TROUBLESHOOTING.md",
      "docs/pages",
      "habitat-lab/habitat/config/README.md",
      "habitat-lab/habitat/config/CONFIG_KEYS.md",
      "habitat-baselines/README.md",
      "habitat-hitl/README.md"
    ],
    "examples": [
      "examples",
      "examples/tutorials",
      "examples/hitl"
    ],
    "tests": [
      "test",
      "habitat-hitl/test"
    ],
    "configs": [
      "habitat-lab/habitat/config",
      "habitat-baselines/habitat_baselines/config",
      "habitat-hitl/habitat_hitl/config"
    ],
    "scripts": [
      "scripts/hab2_bench",
      "scripts/hab3_bench",
      "scripts/habitat_dataset_processing",
      "scripts/generate_profile_shell_scripts.py",
      "scripts/export_smplx_bodies.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source/config/docs paths above changed substantially, run `refresh-repo-skill` even when the commit is unchanged.
- If public package versions, CLI entry points, registry categories, or Habitat-Sim compatibility changed, run `refresh-repo-skill`.
- If the current dirty state includes source changes beyond generated skill artifacts, treat this skill as a baseline that may need refresh.
