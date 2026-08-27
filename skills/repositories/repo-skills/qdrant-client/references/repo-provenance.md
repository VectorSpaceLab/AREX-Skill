# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T00:00:00Z",
  "repository": {
    "name": "qdrant-client",
    "remote_url": "https://github.com/qdrant/qdrant-client",
    "vcs": "git",
    "branch": "master",
    "tag": "v1.18.0",
    "commit": "326adefcc2158121dd0d04877e1a483b5aa2627b",
    "working_tree": "dirty-after-skill-generation",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "qdrant-client",
      "version": "1.18.0",
      "import_names": ["qdrant_client"]
    }
  ],
  "evidence": {
    "source_roots": [
      "qdrant_client",
      "qdrant_client/local",
      "qdrant_client/embed",
      "qdrant_client/uploader",
      "qdrant_client/migrate",
      "qdrant_client/conversions",
      "qdrant_client/http/models",
      "qdrant_client/grpc"
    ],
    "docs": [
      "README.md",
      "tools/DEVELOPMENT.md"
    ],
    "examples": [],
    "tests": [
      "tests/test_qdrant_client.py",
      "tests/test_async_qdrant_client.py",
      "tests/test_in_memory.py",
      "tests/test_local_persistence.py",
      "tests/test_fastembed.py",
      "tests/test_migrate.py",
      "tests/congruence_tests",
      "tests/conversions",
      "tests/embed_tests"
    ],
    "scripts": [
      "tools/generate_async_client.sh",
      "tools/generate_docs.sh",
      "tools/generate_grpc_client.sh",
      "tools/generate_rest_client.sh",
      "tools/populate_inspection_cache.py",
      "tools/populate_inspection_cache.sh",
      "tests/async-client-consistency-check.sh",
      "tests/coverage-test.sh",
      "tests/inspection-cache-consistency-check.sh",
      "tests/integration-tests.sh"
    ],
    "configs": [
      "pyproject.toml",
      "poetry.lock",
      "mypy.ini"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public imports, constructor signatures, generated model classes, or optional extras change, run `refresh-repo-skill`.
- If a checkout has source changes outside generated `skills/` output that affect public APIs, local mode, transport, inference, uploads, migrations, or conversion behavior, run `refresh-repo-skill`.
- If the current working tree is dirty only because generated `skills/` artifacts are present and the source code matches this commit, the runtime guidance still matches the recorded source baseline.
