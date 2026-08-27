# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the ZenML repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-30T00:00:00Z",
  "repository": {
    "name": "zenml",
    "remote_url": "https://github.com/zenml-io/zenml",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d4bc9bc14f8fc04dc62732f5185ae779f5693809",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "zenml",
      "version": "0.95.1",
      "import_names": ["zenml"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/zenml",
      "src/zenml_cli"
    ],
    "docs": [
      "README.md",
      "docs/book",
      "docs/README.md"
    ],
    "examples": [
      "examples/quickstart",
      "examples/deploying_ml_model",
      "examples/deploying_agent",
      "examples/agent_comparison",
      "examples/agent_framework_integrations",
      "examples/hydra_config_management"
    ],
    "tests": [
      "tests/unit",
      "tests/integration/functional",
      "tests/harness",
      "tests/README.md"
    ],
    "scripts": [
      "scripts",
      "zen-dev",
      "zen-test"
    ],
    "agent_guidance": [
      "AGENTS.md",
      "src/zenml/cli/AGENTS.md",
      "src/zenml/integrations/AGENTS.md",
      "src/zenml/models/AGENTS.md",
      "src/zenml/orchestrators/AGENTS.md",
      "src/zenml/zen_server/AGENTS.md",
      "src/zenml/zen_stores/schemas/AGENTS.md",
      "src/zenml/zen_stores/migrations/AGENTS.md",
      "docs/book/AGENTS.md"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the dirty paths are not only generated skill or verification artifacts, run `refresh-repo-skill` before relying on exact implementation details.
- If `pyproject.toml`, console entry points, optional dependency groups, `AGENTS.md` files, major docs, examples, or public APIs changed, run `refresh-repo-skill`.
- If the installed package version differs from `0.95.1`, run the bundled inspection scripts and prefer live package facts over this snapshot.
