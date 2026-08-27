# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, API routes, module metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T17:33:24Z",
  "repository": {
    "name": "Mycodo",
    "remote_url": "https://github.com/kizniche/Mycodo.git",
    "vcs": "git",
    "branch": "master",
    "tag": "v8.17.0",
    "commit": "ee70a111c622e2a81026fd5c1553a948acf8161e",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "Mycodo",
      "version": "8.17.0",
      "import_names": ["mycodo", "alembic_db"]
    }
  ],
  "evidence": {
    "source_roots": ["mycodo", "alembic_db"],
    "docs": ["README.rst", "docs"],
    "examples": ["mycodo/inputs/examples", "mycodo/outputs/examples", "mycodo/functions/examples", "mycodo/actions/examples", "mycodo/widgets/examples"],
    "tests": ["mycodo/tests/software_tests", "mycodo/tests/manual_tests"],
    "configs": ["install", "docker", "mkdocs.yml", "docs_templates"],
    "scripts": ["mycodo/scripts", "install", "docker"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If `MYCODO_VERSION`, `ALEMBIC_VERSION`, REST API routes, module metadata dictionaries, supported-device docs, or installer/service layout changed, refresh even on the same commit.
- If the current working tree has source changes outside generated skill/review artifacts, refresh before relying on detailed API or module-contract guidance.
- If a target installation differs from this source snapshot because it is older/newer than Mycodo 8.17.0, confirm the live `/api` docs and installed module behavior before mutating anything.
