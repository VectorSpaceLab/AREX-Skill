# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of CrewAI. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T00:00:00Z",
  "repository": {
    "name": "crewAI",
    "remote_url": "https://github.com/crewAIInc/crewAI",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9db2d4476641fda3e13347662152214d528f4d79",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "crewai", "version": "1.14.8a2", "import_names": ["crewai"]},
    {"name": "crewai-cli", "version": "1.14.8a2", "import_names": ["crewai_cli"]},
    {"name": "crewai-tools", "version": "1.14.8a2", "import_names": ["crewai_tools"]},
    {"name": "crewai-files", "version": "1.14.8a2", "import_names": ["crewai_files"]},
    {"name": "crewai-core", "version": "1.14.8a2", "import_names": ["crewai_core"]},
    {"name": "crewai-devtools", "version": "1.14.8a2", "import_names": ["crewai_devtools"]}
  ],
  "evidence": {
    "source_roots": [
      "lib/crewai/src/crewai",
      "lib/cli/src/crewai_cli",
      "lib/crewai-tools/src/crewai_tools",
      "lib/crewai-files/src/crewai_files",
      "lib/crewai-core/src/crewai_core",
      "lib/devtools/src/crewai_devtools"
    ],
    "docs": [
      "README.md",
      "docs/edge/en",
      "AGENTS.md"
    ],
    "tests": [
      "lib/crewai/tests",
      "lib/cli/tests",
      "lib/crewai-tools/tests",
      "lib/crewai-files/tests",
      "lib/crewai-core/tests",
      "lib/devtools/tests"
    ],
    "configs": [
      "pyproject.toml",
      "lib/crewai/pyproject.toml",
      "lib/cli/pyproject.toml",
      "lib/crewai-tools/pyproject.toml",
      "lib/crewai-files/pyproject.toml",
      "lib/crewai-core/pyproject.toml",
      "lib/devtools/pyproject.toml",
      "docs/docs.json"
    ],
    "scripts": [
      "scripts/age90_file_input_runner.py",
      "scripts/docs/freeze_current_edge.py",
      "scripts/docs/freeze_historical_versions.py",
      "scripts/docs/prefix_version_paths.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, config, or package metadata changes beyond generated `skills/` artifacts, run `refresh-repo-skill` before relying on API or CLI claims.
- If any package version, optional dependency group, CLI command, or public entry point changes, refresh this skill.
- If `docs/edge/en/` workflow pages change materially, refresh relevant sub-skills even when source code is unchanged.

## Evidence Boundaries

This runtime skill is self-contained. The evidence paths above explain provenance and staleness only; future agents should not need to open those source paths to use the skill. Use the bundled sub-skill references and scripts instead.
