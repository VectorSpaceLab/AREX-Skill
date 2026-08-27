# Repository Provenance

## Purpose

Read this before deciding whether the skill still matches a checkout of
`django-rest-framework-gis`. If the source commit, dirty state, package version,
public entry points, or major evidence paths differ, refresh the repo skill
before relying on detailed behavior.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T19:26:21Z",
  "repository": {
    "name": "django-rest-framework-gis",
    "remote_url": "https://github.com/openwisp/django-rest-framework-gis.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "bcc11537aa7feddc7e083d0765911df21dbd5ed0",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "djangorestframework-gis",
      "version": "1.3.0a0",
      "import_names": ["rest_framework_gis"]
    }
  ],
  "evidence": {
    "source_roots": ["rest_framework_gis"],
    "docs": ["README.rst", "CHANGES.rst", "performance_tests.rst"],
    "examples": [],
    "tests": ["tests/django_restframework_gis_tests"],
    "configs": ["setup.py", "setup.cfg", "pyproject.toml", "tox.ini", ".github/workflows/ci.yml", "Dockerfile", "docker-compose.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale and refresh it.
- If the current working tree is clean or has different relevant dirty paths,
  compare the source rather than assuming the snapshot still applies.
- Refresh when public classes, filter parameters, serializer behavior, schema
  mappings, package dependencies, or compatibility ranges change.
- The `skills/` dirty path in this snapshot is production output and review
  material; it is not evidence that the package source itself was modified.
