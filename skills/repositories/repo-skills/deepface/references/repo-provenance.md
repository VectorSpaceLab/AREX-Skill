# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current commit, dirty state, package version, public APIs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T15:10:00Z",
  "repository": {
    "name": "deepface",
    "remote_url": "https://github.com/serengil/deepface.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4dd71d73a913c155087946480fa02ea430949f1e",
    "working_tree": "dirty-generated-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "deepface", "version": "0.0.100", "import_names": ["deepface"]}
  ],
  "evidence": {
    "source_roots": ["deepface"],
    "docs": ["README.md", ".codeboarding"],
    "examples": ["tests/unit/face-recognition-how.py", "tests/unit/stream.py", "tests/unit/overlay.py", "tests/unit/visual-test.py"],
    "tests": ["tests/unit", "tests/integration"],
    "configs": ["setup.py", "package_info.json", "requirements.txt", "requirements_additional.txt", "requirements_local", ".github/workflows/tests.yml", "Makefile", "Dockerfile", "docker"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If source files, public function signatures, model/detector inventories, API routes, database backend names, or package dependencies changed, refresh the skill even when the commit is similar.
- Generated `skills/` artifacts made the checkout dirty during production; source evidence was taken from the commit above plus the generated artifact context.
