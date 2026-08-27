# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the ADK Python repository. If the current repository commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T00:00:00Z",
  "repository": {
    "name": "adk-python",
    "remote_url": "https://github.com/google/adk-python",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6bc9c9fb78ae0edeecde02fe24e2879f9a96c676",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "google-adk",
      "version": "2.3.0",
      "import_names": [
        "google.adk"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/google/adk"
    ],
    "docs": [
      "README.md",
      "docs/guides"
    ],
    "examples": [
      "contributing/samples"
    ],
    "tests": [
      "tests/unittests",
      "tests/integration"
    ],
    "configs": [
      "pyproject.toml",
      "src/google/adk/agents/config_schemas/AgentConfig.json"
    ],
    "repo_agent_guidance": [
      "AGENTS.md",
      ".agents/skills"
    ],
    "scripts": [
      "scripts/generate_agent_config_schema.py",
      "scripts/check_new_py_files.sh",
      "scripts/db_migration.sh"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has dirty paths beyond generated skill artifacts, compare them to this snapshot and refresh when public APIs, docs, examples, configs, tests, or dependencies changed.
- If `google-adk` package metadata, console entry points, optional extras, config schema, or public import paths changed, refresh this skill.
- If major evidence paths are moved, removed, or substantially rewritten, refresh even when the package version is unchanged.
