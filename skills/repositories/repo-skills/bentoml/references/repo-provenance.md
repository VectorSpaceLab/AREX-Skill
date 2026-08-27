# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of BentoML. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T07:45:09Z",
  "repository": {
    "name": "BentoML",
    "remote_url": "https://github.com/bentoml/BentoML.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "73c4dbead99be6515fa25fcd91e348ac30f5c22e",
    "working_tree": "dirty-generated-skill-output-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "bentoml",
      "version": "0.0.0.post1+g73c4dbead",
      "import_names": ["bentoml", "bentoml_cli"]
    }
  ],
  "evidence": {
    "source_roots": ["src/bentoml", "src/_bentoml_sdk", "src/_bentoml_impl", "src/bentoml_cli"],
    "docs": ["README.md", "docs/source/get-started", "docs/source/build-with-bentoml", "docs/source/reference/bentoml", "docs/source/reference/bentocloud", "docs/source/scale-with-bentocloud"],
    "examples": ["tests/e2e/fixtures/quickstart"],
    "tests": ["tests/e2e/bento_new_sdk", "tests/e2e/bento_server_http", "tests/e2e/bento_server_grpc", "tests/unit", "tests/integration/frameworks"],
    "configs": ["pyproject.toml", "tests/e2e/fixtures/quickstart/bentofile.yaml", "tests/e2e/bento_server_http/bentofile.yaml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If package metadata, public SDK signatures, console command names, or CLI flags changed even on the same commit, refresh the skill.
- If dirty paths include source, docs, tests, examples, or configs other than generated `skills/` output, refresh before trusting detailed workflow guidance.
