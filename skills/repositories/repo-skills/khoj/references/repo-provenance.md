# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T18:42:07Z",
  "repository": {
    "name": "khoj",
    "remote_url": "https://github.com/khoj-ai/khoj.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "9258f57dceab19d52a1a0bdac54eb38576c29187",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "khoj",
      "version": "0.1.dev1",
      "import_names": ["khoj"]
    }
  ],
  "evidence": {
    "source_roots": ["src/khoj", "src/telemetry"],
    "docs": ["README.md", "documentation/docs"],
    "package_metadata": ["pyproject.toml", "uv.lock", "pytest.ini"],
    "deployment_configs": ["docker-compose.yml", "Dockerfile", "prod.Dockerfile", "computer.Dockerfile", "gunicorn-config.py", "manifest.json", "versions.json"],
    "scripts": ["scripts/dev_setup.sh", "scripts/bump_version.sh"],
    "tests": ["tests", "tests/data"],
    "sampled_interfaces": ["src/interface"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current dirty paths differ from `dirty_paths`, run `refresh-repo-skill` before relying on detailed behavior claims.
- If `pyproject.toml`, console entry points, router modules, content processors, search filters, chat/agent schemas, scheduler/memory APIs, or contributor/test workflows changed, refresh even if the commit appears unchanged.
- If package metadata reports a different `khoj` version or supported Python range, refresh the install/deployment guidance.
