# Repository Provenance

## Purpose

Read this before deciding whether this TaskingAI skill is current for a checkout of the repository. If the current repo commit, dirty state, package/component versions, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T08:11:29Z",
  "repository": {
    "name": "TaskingAI",
    "remote_url": "https://github.com/TaskingAI/TaskingAI.git",
    "vcs": "git",
    "branch": "master",
    "tag": "plugin-v0.2.13",
    "commit": "f0092d6b2dd82e98e188e0b9849fdd4c7230dd98",
    "working_tree": "clean-before-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "taskingai-backend-service",
      "version": "v0.3.0",
      "import_names": ["app", "tkhelper"]
    },
    {
      "name": "taskingai-inference-service",
      "version": "v0.2.20",
      "import_names": ["app", "providers", "provider_dependency"]
    },
    {
      "name": "taskingai-plugin-service",
      "version": "v0.2.13",
      "import_names": ["app", "bundles", "bundle_dependency"]
    },
    {
      "name": "taskingai-client-sdk",
      "version": null,
      "import_names": ["taskingai"]
    }
  ],
  "evidence": {
    "source_roots": [
      "backend/app",
      "backend/tkhelper",
      "inference/app",
      "inference/providers",
      "inference/provider_dependency",
      "plugin/app",
      "plugin/bundles",
      "plugin/bundle_dependency"
    ],
    "docs": [
      "README.md",
      "docker/README.md"
    ],
    "examples": [
      "docker/docker-compose.yml",
      "docker/.env.example",
      "backend/.env.example",
      "inference/.env.example",
      "plugin/.env.example"
    ],
    "tests": [
      "backend/tests",
      "backend/run_api_test.sh",
      "backend/run_web_test.sh",
      "inference/test",
      "plugin/test"
    ],
    "configs": [
      "backend/app/config.py",
      "inference/config.py",
      "plugin/config.py",
      "frontend/package.json"
    ]
  },
  "verification_summary": {
    "inspection_python": "3.10",
    "backend_imports": "passed with non-fatal Pydantic warnings",
    "inference_imports": "passed",
    "plugin_imports": "passed",
    "python_3_11_backend_import": "failed due aioredis==2.0.1 duplicate TimeoutError base class",
    "native_service_tests": "not run; require Docker/services/credentials/storage/network"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current source checkout has uncommitted changes outside generated skill/review artifacts, run `refresh-repo-skill` or re-check the affected sub-skill.
- If service versions, route families, provider schemas, plugin bundles, Docker image tags, or environment contracts changed, refresh before relying on detailed workflow guidance.
- If Python dependencies changed, re-verify backend/import behavior; in this snapshot, Python 3.10 is the verified backend inspection path.
