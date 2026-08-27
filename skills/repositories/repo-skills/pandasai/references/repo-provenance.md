# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
PandasAI. If the current repo commit, dirty state, package version, entry points,
or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:12:31Z",
  "repository": {
    "name": "pandas-ai",
    "remote_url": "https://github.com/sinaptik-ai/pandas-ai.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "bbbb771d31062d81f6fa19bafb40620d5cbe48f4",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pandasai",
      "version": "3.0.0",
      "import_names": ["pandasai"]
    }
  ],
  "evidence": {
    "source_roots": [
      "pandasai",
      "pandasai/ee/skills"
    ],
    "docs": [
      "README.md",
      "docs/v3"
    ],
    "examples": [
      "examples/quickstart.ipynb",
      "examples/semantic_layer_csv.ipynb",
      "examples/docker_sandbox.ipynb",
      "examples/data"
    ],
    "tests": [
      "tests/unit_tests",
      "tests/integration_tests"
    ],
    "configs": [
      "pyproject.toml",
      "pytest.ini",
      "Makefile",
      "CONTRIBUTING.md"
    ],
    "extension_metadata": [
      "extensions/llms/litellm/README.md",
      "extensions/llms/openai/README.md",
      "extensions/connectors/sql/README.md",
      "extensions/sandbox/docker/README.md"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has source or documentation changes that were not
  present in this snapshot, run `refresh-repo-skill`.
- If package metadata, console entry points, public imports, optional extension
  names, or docs for v3 workflows changed, run `refresh-repo-skill`.
