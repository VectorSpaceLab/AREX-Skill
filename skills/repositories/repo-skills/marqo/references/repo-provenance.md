# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T18:01:26Z",
  "repository": {
    "name": "marqo",
    "remote_url": "https://github.com/marqo-ai/marqo.git",
    "vcs": "git",
    "branch": "mainline",
    "tag": null,
    "commit": "37a728385a25c4572a8f47b5327e6a7c946d94a9",
    "working_tree": "dirty-generated-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "marqo-api",
      "version": "0.0.1",
      "import_names": ["marqo"]
    },
    {
      "name": "marqo-common",
      "version": "0.1.0",
      "import_names": ["marqo_common"]
    },
    {
      "name": "marqo-inference-orchestrator",
      "version": "0.0.1",
      "import_names": ["inference_orchestrator"]
    },
    {
      "name": "marqo-model-management",
      "version": "0.0.1",
      "import_names": ["model_management"]
    }
  ],
  "evidence": {
    "source_roots": [
      "components/common/src/marqo_common",
      "components/marqo/src/marqo",
      "components/inference_orchestrator/src/inference_orchestrator",
      "components/model_management/src/model_management"
    ],
    "docs": [
      "README.md",
      "CLAUDE.md",
      "CONTRIBUTING.md",
      "components/marqo/src/marqo/README.md",
      "components/inference_orchestrator/README.md",
      "components/*/CLAUDE.md"
    ],
    "examples": ["examples"],
    "tests": [
      "components/marqo/tests/unit_tests",
      "components/marqo/tests/integ_tests",
      "components/marqo/tests/api_tests/v1/tests/api_tests",
      "components/inference_orchestrator/tests",
      "components/model_management/tests"
    ],
    "configs": [
      "components/*/pyproject.toml",
      "compose.yaml",
      "compose-inference.yaml",
      "compose-model-management.yaml",
      "compose-triton.yaml",
      ".env"
    ],
    "scripts_and_service_artifacts": [
      "components/marqo/scripts/vespa_local",
      "components/marqo/vespa",
      "components/marqo/run_marqo.sh",
      "components/marqo/tests/api_tests/v1/scripts"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
- If the current checkout's dirty paths include source, docs, tests, pyproject, compose, Vespa, or script changes beyond generated skill artifacts, refresh before relying on detailed API/schema guidance.
- If Marqo OSS deprecation status or the supported deployment topology changed, refresh the local-development and package-map references.
