# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Dagster. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "dagster",
    "remote_url": "https://github.com/dagster-io/dagster",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4fb00173b453ac4151c88454e30b567af14c1808",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {"name": "dagster", "version": "1!0+dev", "import_names": ["dagster"]},
    {"name": "dagster-pipes", "version": "1!0+dev", "import_names": ["dagster_pipes"]},
    {"name": "dagster-graphql", "version": "1!0+dev", "import_names": ["dagster_graphql"]},
    {"name": "dagster-webserver", "version": "1!0+dev", "import_names": ["dagster_webserver"]},
    {"name": "dagster-shared", "version": "1!0+dev", "import_names": ["dagster_shared"]}
  ],
  "evidence": {
    "source_roots": [
      "python_modules/dagster",
      "python_modules/dagster-pipes",
      "python_modules/dagster-graphql",
      "python_modules/dagster-webserver",
      "python_modules/libraries/dagster-shared",
      "python_modules/libraries/dagster-dg-core",
      "python_modules/libraries/dagster-dg-cli",
      "python_modules/libraries/create-dagster"
    ],
    "docs": [
      "docs/docs/getting-started",
      "docs/docs/dagster-basics-tutorial",
      "docs/docs/guides",
      "docs/docs/deployment",
      "docs/docs/api",
      "docs/docs/examples",
      "docs/docs/integrations/external-pipelines"
    ],
    "examples": [
      "examples/quickstart_etl",
      "examples/docs_snippets",
      "examples/project_fully_featured",
      "examples/assets_dynamic_partitions",
      "examples/assets_smoke_test",
      "examples/development_to_production",
      "examples/deploy_docker",
      "examples/deploy_ecs",
      "examples/deploy_k8s"
    ],
    "tests": [
      "python_modules/dagster/dagster_tests/asset_defs_tests",
      "python_modules/dagster/dagster_tests/core_tests",
      "python_modules/dagster/dagster_tests/cli_tests",
      "python_modules/dagster/dagster_tests/components_tests",
      "python_modules/dagster-pipes/dagster_pipes_tests",
      "python_modules/dagster-graphql/dagster_graphql_tests"
    ],
    "configs": ["pyproject.toml", "CLAUDE.md", ".claude/python_packages.md", ".claude/dev_workflow.md", ".claude/coding_conventions.md", ".claude/ui_workflow.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If source-code, docs, examples, package metadata, public entry points, or selected tests changed even on the same commit, refresh before relying on detailed claims.
- Generated skill output created by this run is not source evidence drift by itself.
- If `dagster-dg-core`, `dagster-dg-cli`, or `create-dagster` dependency metadata changes, refresh the `components-projects` coverage because this snapshot recorded an unpublished `dagster-cloud-cli==1!0+dev` caveat.
